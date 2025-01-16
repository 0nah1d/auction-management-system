import json
import os
from django.contrib.auth import login, logout
from django.db.models import Count, Max, Min
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse
from django.shortcuts import render, get_object_or_404
from .models import *
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Prefetch
from .forms import *
from django.contrib.auth.forms import AuthenticationForm
from django.utils.timezone import now, make_aware, get_default_timezone
from django.core.files.storage import default_storage
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


def index(request):
    def add_full_image_url_and_highest_bid(auction_list):
        for auction in auction_list:
            # Get the first image URL
            first_image = AuctionImage.objects.filter(auction=auction).first()
            if first_image:
                auction.first_image_url = request.build_absolute_uri(first_image.image_url.url)
            else:
                auction.first_image_url = None

            # Get the highest bid
            auction.highest_bid = auction.get_highest_bid()

        return auction_list

    top_three_products = AuctionList.objects.filter(active_bool=True).order_by('-buy_now_price')[:4]
    watch_cat_products = AuctionList.objects.filter(active_bool=True, categories__slug='watch')[:4]

    # Add first image URL and highest bid to each auction
    top_three_products = add_full_image_url_and_highest_bid(top_three_products)
    watch_cat_products = add_full_image_url_and_highest_bid(watch_cat_products)

    context = {
        'header_bg': True,
        'top_three_products': top_three_products,
        'watch_cat_products': watch_cat_products,
    }
    return render(request, "index.html", context)


def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect(reverse("index"))
        else:
            return render(request, "register.html", {
                "form": form
            })
    else:
        form = CustomUserCreationForm()
        return render(request, "register.html", {
            "form": form
        })


def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect(reverse("index"))
    else:
        form = AuthenticationForm(request)

    return render(request, "login.html", {"form": form})


def contact(request):
    return render(request, "contact.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def auction_list(request):
    search_query = request.GET.get('q', '')
    selected_category = request.GET.get('filter-by', 'all')

    auctions = AuctionList.objects.filter(active_bool=True)

    if search_query:
        auctions = auctions.filter(Q(title__icontains=search_query))

    if selected_category != 'all':
        auctions = auctions.filter(categories__title=selected_category)

    auctions = auctions.prefetch_related(
        Prefetch('images', queryset=AuctionImage.objects.order_by('id'))
    )

    paginator = Paginator(auctions, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    total_auctions = paginator.count

    for auction in page_obj:
        first_image = auction.images.first()
        if first_image:
            auction.first_image_url = request.build_absolute_uri(first_image.image_url.url)
        else:
            auction.first_image_url = None

        auction.highest_bid = auction.get_highest_bid()

    categories = Category.objects.all()
    return render(request, "list.html", {
        'auctions': page_obj,
        'categories': categories,
        'selected_category': selected_category,
        'total_auctions': total_auctions
    })


def minbid(min_bid, present_bid):
    for bids_list in present_bid:
        if min_bid < int(bids_list.bid):
            min_bid = int(bids_list.bid)
    return min_bid


def auction_details(request, list_id):
    # Fetch the auction listing
    auction = get_object_or_404(AuctionList, pk=list_id, active_bool=True)

    # Fetch associated images
    images = AuctionImage.objects.filter(auction=auction)
    image_urls = [request.build_absolute_uri(image.image_url.url) for image in images if image.image_url]

    # Fetch bids and related information
    bids_present = Bids.objects.filter(auction=auction)
    total_bids = bids_present.count()
    total_bidders = Bids.objects.filter(auction=auction).values('user').annotate(total_bids=Count('user')).count()

    # Get the highest bid
    highest_bid = auction.get_highest_bid()

    comments = Comments.objects.filter(listing=auction)
    for comment in comments:
        comment.user_photo = comment.user.profile_picture.url if comment.user.profile_picture else None
    rating_range = range(1, 6)

    context = {
        "list": auction,
        "image_urls": image_urls,
        "comments": comments,
        "rating_range": rating_range,
        "present_bid": minbid(auction.starting_bid, bids_present),
        "total_bids": total_bids,
        "total_bidders": total_bidders,
        "highest_bid": highest_bid,  # Add highest bid to context
        "is_owner": auction.user == request.user,
        "is_payment": Payment.objects.filter(auction=auction, status="VALID").exists()
    }
    return render(request, "details.html", context)


@login_required
def edit_profile_picture(request):
    user = request.user

    if request.method == 'POST' and request.FILES.get('profile_picture'):
        new_picture = request.FILES['profile_picture']

        # Remove the previous profile picture if there is one
        if user.profile_picture:
            if default_storage.exists(user.profile_picture.name):
                default_storage.delete(user.profile_picture.name)

        # Update the user's profile picture
        user.profile_picture = new_picture
        user.save()

        return JsonResponse({'success': True})

    return JsonResponse({'success': False}, status=400)


@login_required(login_url='login')
def create(request):
    if request.method == "POST":
        title = request.POST.get("create_title")
        desc = request.POST.get("create_desc")
        starting_bid = request.POST.get("create_initial_bid")
        buy_now_price = request.POST.get("create_buy_now_price")
        expire_date = request.POST.get("expire_date")
        selected_category_slugs = request.POST.getlist("category[]")

        if not title or not desc or not starting_bid or not expire_date:
            messages.error(request, "All required fields must be filled out.")
            return redirect("create")

        # Create new auction
        auction = AuctionList.objects.create(
            title=title,
            desc=desc,
            starting_bid=starting_bid,
            buy_now_price=buy_now_price,
            expire_date=expire_date,
            user=request.user
        )

        # Handle categories
        for slug in selected_category_slugs:
            if slug == "new":
                new_category_title = request.POST.get("new_category_title")
                if new_category_title:
                    category_slug = new_category_title.lower().replace(' ', '-')
                    category, created = Category.objects.get_or_create(
                        slug=category_slug,
                        defaults={'title': new_category_title}
                    )
                    auction.categories.add(category)
                else:
                    messages.error(request, "New category title cannot be empty.")
                    return redirect('create')
            else:
                try:
                    category = Category.objects.get(slug=slug)
                    auction.categories.add(category)
                except Category.DoesNotExist:
                    messages.error(request, f"Category with slug '{slug}' does not exist.")
                    return redirect('create')

        # Handle image uploads
        if 'img_url' in request.FILES:
            uploaded_files = request.FILES.getlist('img_url')
            for file in uploaded_files:
                AuctionImage.objects.create(auction=auction, image_url=file)

        messages.success(request, "Auction created successfully.")
        return redirect('create')

    user = request.user

    profile_picture_url = None
    if user.profile_picture:
        profile_picture_url = request.build_absolute_uri(user.profile_picture.url)

    return render(request, "create.html", {
        'categories': Category.objects.all(),
        'email': user.email,
        'name': f"{user.first_name} {user.last_name}",
        'profile_picture': profile_picture_url,
    })


@login_required(login_url='login')
def dashboard(request):
    user_bids = Bids.objects.filter(user=request.user)
    user_win = Winner.objects.filter(user=request.user)
    user_total_auction = AuctionList.objects.filter(user=request.user)

    user = request.user

    profile_picture_url = None
    if user.profile_picture:
        profile_picture_url = request.build_absolute_uri(user.profile_picture.url)

    return render(request, "dashboard.html", {
        'email': user.email,
        'name': f"{user.first_name} {user.last_name}",
        'profile_picture': profile_picture_url,
        'your_win': len(user_win),
        'your_total_auction': len(user_total_auction),
        'active_bids': len(user_bids)
    })


@login_required(login_url='login')
def bid(request):
    bid_amnt = request.GET["bid_amnt"]
    list_id = request.GET["list_id"]

    if not bid_amnt or not list_id:
        messages.error(request, "Bid amount or listing ID is missing.")
        return redirect("auctionDetails", list_id)

        # Fetch the auction listing
    auction_listing = get_object_or_404(AuctionList, pk=list_id)

    if auction_listing.user == request.user:
        messages.warning(request, "You cannot bid on your own auction.")
        return redirect("auctionDetails", list_id)

    payments = Payment.objects.filter(auction=auction_listing)

    if any(payment.status == "VALID" for payment in payments):
        messages.info(request, "Already paid for this auction.")
        return redirect('auctionDetails', list_id)

    try:
        winner = Winner.objects.get(bid_win_list=auction_listing)
    except Winner.DoesNotExist:
        winner = None

    if winner:
        messages.warning(request, "This auction has already been won, so you can no longer place a bid.")
        return redirect("auctionDetails", list_id)

    # Get the current time in UTC
    current_time = now()

    # Convert expire_date to UTC if it's offset-naive
    expire_date = auction_listing.expire_date
    if not expire_date.tzinfo:
        expire_date = make_aware(expire_date, get_default_timezone())

    # Check if the auction has expired
    if current_time > expire_date:
        messages.warning(request, "Sorry, the auction for this listing has expired.")
        return redirect("auctionDetails", list_id)

    # Proceed with bid validation
    bids_present = Bids.objects.filter(auction=auction_listing)
    starting_bid = auction_listing.starting_bid
    min_req_bid = minbid(starting_bid, bids_present)  # Assuming `minbid` is a custom function you have implemented

    if int(bid_amnt) > int(min_req_bid):
        mybid = Bids(user=request.user, auction=auction_listing, bid=bid_amnt)
        mybid.save()
        messages.success(request, "Bid placed successfully.")
        return redirect("auctionDetails", list_id)

    messages.warning(request, f"Sorry, {bid_amnt} is less. It should be more than {min_req_bid}$.")
    return redirect("auctionDetails", list_id)


# shows message abt winner when bid is closed
@login_required(login_url='login')
def win_ner(request):
    bid_id = request.GET.get("listid")

    try:
        # Fetch the auction based on the provided bid ID
        biddesc = AuctionList.objects.get(pk=bid_id, active_bool=True)
        bids_present = Bids.objects.filter(auction=biddesc)

        if not bids_present.exists():
            messages.error(request, "No bids found for this auction. So you can't close it.")
            return redirect("auctionDetails", bid_id)

        max_bid = minbid(biddesc.starting_bid, bids_present)

        # Get the winning bid and user
        winner_object = Bids.objects.get(bid=max_bid, auction=biddesc)
        winner_user = winner_object.user

        # Check if the winner is the owner of the auction
        if winner_user == biddesc.user:
            messages.error(request, "The auction owner cannot win their own bid.")
            return redirect("myAuction")

        # Save winner details
        Winner.objects.create(bid_win_list=biddesc, user=winner_user)
        messages.success(request, f"{winner_user.username} won {biddesc.title}.")

        # Deactivate the auction
        biddesc.active_bool = False
        biddesc.save()

    except AuctionList.DoesNotExist:
        messages.error(request, "Auction not found.")
    return redirect("myAuction")


# checks winner
def winnings(request):
    try:
        your_win = Winner.objects.filter(user=request.user.pk)
    except:
        your_win = None

    return render(request, "winnings.html", {
        "user_winlist": your_win,
    })


@login_required(login_url='login')
def user_bid(request):
    userBids = Bids.objects.filter(user=request.user)
    user_auctions = AuctionList.objects.filter(id__in=[bid.auction_id for bid in userBids])

    for auction in user_auctions:
        # Fetch the first image URL for the auction
        first_image = AuctionImage.objects.filter(auction=auction).first()
        if first_image:
            auction.image_url = request.build_absolute_uri(first_image.image_url.url)
        else:
            auction.image_url = None

        # Add total bids count
        auction.total_bids = Bids.objects.filter(auction=auction).count()

        # Find the current (highest) bid for this auction
        current_bid = Bids.objects.filter(auction=auction).aggregate(Max('bid'))['bid__max']
        auction.current_bid = current_bid if current_bid is not None else 0

    # Pagination
    paginator = Paginator(user_auctions, 5)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    total_auctions = paginator.count

    user = request.user

    # Get profile picture URL
    profile_picture_url = None
    if user.profile_picture:
        profile_picture_url = request.build_absolute_uri(user.profile_picture.url)

    return render(request, "my-bid.html", {
        'email': user.email,
        'name': f"{user.first_name} {user.last_name}",
        'profile_picture': profile_picture_url,
        'userBids': user_auctions,
        'user_auctions': page_obj,
        'total_auctions': total_auctions
    })


@login_required(login_url='login')
def user_profile(request):
    user = request.user

    profile_picture_url = None
    if user.profile_picture:
        profile_picture_url = request.build_absolute_uri(user.profile_picture.url)

    # Check if the user has an associated address
    address_info = None
    if user.address:
        address_info = {
            'province': user.province,
            'city': user.city,
            'zone': user.zone,
            'address': user.address,
            'zip_code': user.zip_code,
            'phone': user.phone,
        }

    context = {
        'username': user.username,
        'email': user.email,
        'name': f"{user.first_name} {user.last_name}",
        'profile_picture': profile_picture_url,
        'address': address_info,
    }
    return render(request, "profile.html", context)


@login_required(login_url='login')
def edit_profile(request):
    user = request.user

    # Instantiate the user form with the current user's data
    user_form = UserProfileForm(instance=user)

    if request.method == 'POST':
        user_form = UserProfileForm(request.POST, request.FILES, instance=user)

        if user_form.is_valid():
            user_form.save()  # Save the updated user data
            messages.success(request, 'Your profile has been updated successfully.')
            return redirect('userProfile')  # Redirect to profile view

    # Prepare the context for rendering the template
    context = {
        'user_form': user_form,
        'profile_picture': user.profile_picture.url if user.profile_picture else None,
        'name': f"{user.first_name} {user.last_name}",
    }
    return render(request, 'edit_profile.html', context)


@login_required(login_url='login')
def user_win_bids(request):
    # Retrieve all winning bids for the logged-in user
    win_lists = Winner.objects.filter(user=request.user)

    auctions = []
    for win in win_lists:
        auction = AuctionList.objects.get(id=win.bid_win_list.pk)

        # Get the first image URL if available
        first_image = AuctionImage.objects.filter(auction=auction).first()
        image_url = request.build_absolute_uri(first_image.image_url.url) if first_image else None

        # Retrieve all payments for this auction and user
        payments = Payment.objects.filter(auction=auction, user=request.user)
        payment_status = "Pending"  # Default status

        # Check if any payment has a "VALID" status
        if any(payment.status == "VALID" for payment in payments):
            payment_status = "VALID"

        auctions.append({
            'id': auction.id,
            'title': auction.title,
            'starting_bid': auction.starting_bid,
            'highest_bid': auction.get_highest_bid(),
            'buy_now_price': auction.buy_now_price,
            'expire_date': auction.expire_date,
            'image_url': image_url,
            'payment_status': payment_status
        })

    # Pagination
    paginator = Paginator(win_lists, 5)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    total_auctions = paginator.count

    user = request.user
    profile_picture_url = None
    if hasattr(user, 'profile_picture') and user.profile_picture:
        profile_picture_url = request.build_absolute_uri(user.profile_picture.url)

    return render(request, "winning-bids.html", {
        'email': user.email,
        'name': f"{user.first_name} {user.last_name}",
        'profile_picture': profile_picture_url,
        'auctions': auctions,
        'win_auctions': page_obj,
        'total_auctions': total_auctions
    })


@login_required(login_url='login')
def myauction(request):
    # Fetch auctions for the current user and annotate with bid count
    auctions = AuctionList.objects.filter(user=request.user).annotate(total_bids=Count('bids'))

    # Prepare auction data
    auction_list = []
    for auction in auctions:
        first_image = AuctionImage.objects.filter(auction=auction).first()
        first_image_url = request.build_absolute_uri(first_image.image_url.url) if first_image else None

        auction_list.append({
            'id': auction.id,
            'title': auction.title,
            'starting_bid': auction.starting_bid,
            'highest_bid': auction.get_highest_bid(),
            'buy_now_price': auction.buy_now_price,
            'bid_watch_list': auction.bid_watch_list,
            'expire_date': auction.expire_date,
            'image_url': first_image_url,
            'active_status': auction.active_bool,
            'total_bids': auction.total_bids
        })

    # Get user profile picture URL
    user = request.user
    profile_picture_url = None
    if user.profile_picture:
        profile_picture_url = request.build_absolute_uri(user.profile_picture.url)

    # Pagination
    paginator = Paginator(auction_list, 5)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    total_auctions = paginator.count

    # Render the template
    return render(request, "myauction.html", {
        'email': user.email,
        'name': f"{user.first_name} {user.last_name}",
        'profile_picture': profile_picture_url,
        'auctions': page_obj,
        'total_auctions': total_auctions
    })


@login_required(login_url='login')
def delete_auction(request, auction_id):
    auction = get_object_or_404(AuctionList, id=auction_id)

    if auction.user == request.user:
        auction.delete()
        messages.success(request, "Auction deleted successfully")
    else:
        messages.error(request, "You are not authorized to delete this auction")

    return redirect("myAuction")


@login_required(login_url='login')
def update(request, auction_id):
    auction = get_object_or_404(AuctionList, id=auction_id)

    if request.method == "POST":
        title = request.POST.get("create_title")
        desc = request.POST.get("create_desc")
        starting_bid = request.POST.get("create_initial_bid")
        buy_now_price = request.POST.get("create_buy_now_price")
        expire_date = request.POST.get("expire_date")

        if not title or not desc or not starting_bid or not expire_date:
            messages.error(request, "All required fields must be filled out.")
            return redirect("update", auction_id=auction_id)

        # Update auction
        auction.title = title
        auction.desc = desc
        auction.starting_bid = starting_bid
        auction.buy_now_price = buy_now_price
        auction.expire_date = expire_date
        auction.save()

        selected_category_slugs = request.POST.getlist("category[]")

        # Handle categories
        for slug in selected_category_slugs:
            if slug == "new":
                new_category_title = request.POST.get("new_category_title")
                if new_category_title:
                    category_slug = new_category_title.lower().replace(' ', '-')
                    category, created = Category.objects.get_or_create(
                        slug=category_slug,
                        defaults={'title': new_category_title}
                    )
                    auction.categories.add(category)
                else:
                    messages.error(request, "New category title cannot be empty.")
                    return redirect('create')
            else:
                try:
                    category = Category.objects.get(slug=slug)
                    auction.categories.add(category)
                except Category.DoesNotExist:
                    messages.error(request, f"Category with slug '{slug}' does not exist.")
                    return redirect('create')

        # Handle image uploads
        if 'img_url' in request.FILES:
            uploaded_files = request.FILES.getlist('img_url')
            for file in uploaded_files:
                AuctionImage.objects.create(auction=auction, image_url=file)

        messages.success(request, "Auction updated successfully.")
        return redirect('myAuction')

    # Get existing images for the auction
    image_urls = [image.image_url.url for image in auction.images.all()]

    return render(request, "update.html", {
        'auction': auction,
        'categories': Category.objects.all(),
        'image_urls': image_urls
    })


@csrf_exempt
def remove_image(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        image_url = data.get('image_url')
        auction_id = data.get('auction_id')

        if not image_url or not auction_id:
            return JsonResponse({'status': 'error', 'message': 'Invalid request data'}, status=400)

        file_name = os.path.basename(image_url)

        try:
            auction_image = AuctionImage.objects.get(
                auction_id=auction_id,
                image_url__endswith=file_name
            )
            auction_image.delete()
            return JsonResponse({'status': 'success', 'message': 'Image removed successfully'})
        except AuctionImage.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Image not found'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required(login_url='login')
def payment_information(request):
    user = request.user
    profile_picture_url = None
    if hasattr(user, 'profile_picture') and user.profile_picture:
        profile_picture_url = request.build_absolute_uri(user.profile_picture.url)

    payments = Payment.objects.filter(user=user).order_by('-transaction_date')

    # Pagination
    paginator = Paginator(payments, 5)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    total_payment = paginator.count

    return render(request, "payment_information.html", {
        'email': user.email,
        'name': f"{user.first_name} {user.last_name}",
        'profile_picture': profile_picture_url,
        'payments': page_obj,
        'total_payment': total_payment
    })


@login_required(login_url='login')
def comment(request):
    if request.method == "POST":
        list_id = request.POST.get("list_id")
        comment_text = request.POST.get('comment')
        rating = request.POST.get('rating')

        # Validate data
        if not list_id or not comment_text or not rating:
            messages.error(request, "Missing required fields")
            return redirect('auctionDetails', list_id=list_id)

        # Fetch the listing and user
        try:
            listing = AuctionList.objects.get(id=list_id)
        except AuctionList.DoesNotExist:
            messages.error(request, "Listing not found")
            return redirect('auctionDetails', list_id=list_id)

        user = request.user

        # Create a new comment
        new_comment = Comments(user=user, listing=listing, comment=comment_text, rating=rating)
        new_comment.save()

        return redirect('auctionDetails', list_id=list_id)
    else:
        messages.error(request, "Invalid request method")
        return redirect('auctionDetails', list_id=request.POST.get('list_id', ''))


@login_required(login_url='login')
def shipping_to(request):
    user = request.user
    profile_picture_url = getattr(user.profile_picture, 'url', None)
    if profile_picture_url:
        profile_picture_url = request.build_absolute_uri(profile_picture_url)

    # Shipping addresses where the user is the sender
    shipping_addresses = (
        ShippingAddress.objects
        .filter(auction__user=user)
        .order_by('-created_at')
    )

    paginator = Paginator(shipping_addresses, 5)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "shipping_to.html", {
        'email': user.email,
        'name': f"{user.first_name} {user.last_name}",
        'profile_picture': profile_picture_url,
        'shipping_addresses': page_obj,
        'total_to': paginator.count
    })


@login_required(login_url='login')
def shipping_from(request):
    user = request.user
    profile_picture_url = getattr(user.profile_picture, 'url', None)
    if profile_picture_url:
        profile_picture_url = request.build_absolute_uri(profile_picture_url)

    # Shipping addresses where the user is the receiver
    shipping_addresses = (
        ShippingAddress.objects
        .filter(user=user)
        .select_related('auction__user')
        .order_by('-created_at')
    )

    paginator = Paginator(shipping_addresses, 5)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "shipping_from.html", {
        'email': user.email,
        'name': f"{user.first_name} {user.last_name}",
        'profile_picture': profile_picture_url,
        'shipping_addresses': page_obj,
        'total_from': paginator.count
    })


def update_shipping_status(request, address_id):
    address = get_object_or_404(ShippingAddress, id=address_id)

    if request.method == 'POST' and 'status' in request.POST:
        new_status = request.POST['status']
        if new_status in dict(ShippingAddress.STATUS_CHOICES).keys():
            address.status = new_status
            address.save()
            messages.success(request, "Shipping status updated successfully.")
        else:
            messages.error(request, "Invalid status selection.")

    return redirect('shipping_to')
