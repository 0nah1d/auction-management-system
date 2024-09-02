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
from django.db.models import Q
from .forms import CustomUserCreationForm
from django.contrib.auth.forms import AuthenticationForm
from django.utils.timezone import now, make_aware, get_default_timezone
from django.core.files.storage import default_storage
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.csrf import csrf_exempt


def index(request):
    def add_full_image_url(auction_list):
        for auction in auction_list:
            first_image = AuctionImage.objects.filter(auction=auction).first()
            if first_image:
                auction.first_image_url = request.build_absolute_uri(first_image.image_url.url)
            else:
                auction.first_image_url = None
        return auction_list

    top_three_products = AuctionList.objects.filter(active_bool=True).order_by('-buy_now_price')[:3]
    watch_cat_products = AuctionList.objects.filter(active_bool=True, categories__slug='watch')[:3]

    # Add first image URL to each auction
    top_three_products = add_full_image_url(top_three_products)
    watch_cat_products = add_full_image_url(watch_cat_products)

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
            # Authenticate the user
            user = form.get_user()
            login(request, user)
            return redirect(reverse("userProfile"))
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

    paginator = Paginator(auctions, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    total_auctions = paginator.count

    for auction in page_obj:
        first_image = AuctionImage.objects.filter(auction=auction).first()
        if first_image:
            auction.first_image_url = request.build_absolute_uri(first_image.image_url.url)
        else:
            auction.first_image_url = None

    categories = Category.objects.all()
    return render(request, "list.html", {
        'auctions': page_obj,
        'categories': categories,
        'selected_category': selected_category,
        'total_auctions': total_auctions
    })


def auction_details(request, bidid):
    biddesc = get_object_or_404(AuctionList, pk=bidid, active_bool=True)

    images = AuctionImage.objects.filter(auction=biddesc)

    image_urls = [request.build_absolute_uri(image.image_url.url) for image in images if image.image_url]

    bids_present = Bids.objects.filter(listingid=bidid)
    total_bids = Bids.objects.filter(listingid=bidid)
    total_bidders = Bids.objects.filter(listingid=bidid).values('user').annotate(total_bids=Count('user'))

    return render(request, "details.html", {
        "list": biddesc,
        "image_urls": image_urls,
        "comments": Comments.objects.filter(listingid=bidid),
        "present_bid": minbid(biddesc.starting_bid, bids_present),
        "total_bids": len(total_bids),
        "total_bidders": len(total_bidders),
        "is_owner": biddesc.user == request.user
    })


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

    return render(request, "create.html", {'categories': Category.objects.all()})


@login_required(login_url='login')
def dashboard(request):
    userBids = Bids.objects.filter(user=request.user)
    user_auctions = AuctionList.objects.filter(id__in=[bid.listingid for bid in userBids])
    your_win = Winner.objects.filter(user=request.user.pk)

    # Get highest and lowest bid prices for each auction
    for auction in user_auctions:
        highest_bid = Bids.objects.filter(listingid=auction.id).aggregate(Max('bid'))
        lowest_bid = Bids.objects.filter(listingid=auction.id).aggregate(Min('bid'))

        auction.highest_bid_price = highest_bid if highest_bid is not None else 0
        auction.lowest_bid_price = lowest_bid if lowest_bid is not None else 0

    user = request.user

    profile_picture_url = None
    if user.profile_picture:
        profile_picture_url = request.build_absolute_uri(user.profile_picture.url)

    return render(request, "dashboard.html", {
        'email': user.email,
        'name': f"{user.first_name} {user.last_name}",
        'profile_picture': profile_picture_url,
        'auctions': user_auctions,
        'your_win': len(your_win),
        'active_bids': len(userBids)
    })


def listingpage(request, bidid):
    biddesc = AuctionList.objects.get(pk=bidid, active_bool=True)
    bids_present = Bids.objects.filter(listingid=bidid)
    total_bids = Bids.objects.filter(listingid=bidid)
    total_bidders = Bids.objects.filter(listingid=bidid).values('user').annotate(
        total_bids=Count('user'))

    return render(request, "details.html", {
        "list": biddesc,
        "comments": Comments.objects.filter(listingid=bidid),
        "present_bid": minbid(biddesc.starting_bid, bids_present),
    })


@login_required(login_url='login')
def watchlistpage(request, username):
    # present_w = watchlist.objects.get(user = "username")
    list_ = Watchlist.objects.filter(user=username)
    return render(request, "watchlist.html", {
        "user_watchlist": list_,
    })


# this function returns minimum bid required to place a user's bid
def minbid(min_bid, present_bid):
    for bids_list in present_bid:
        if min_bid < int(bids_list.bid):
            min_bid = int(bids_list.bid)
    return min_bid


@login_required(login_url='login')
def bid(request):
    bid_amnt = request.GET["bid_amnt"]
    list_id = request.GET["list_d"]

    # Fetch the auction listing
    auction_listing = AuctionList.objects.get(pk=list_id)

    if auction_listing.user == request.user:
        messages.warning(request, "You cannot bid on your own auction.")
        return redirect("auctionDetails", list_id)

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
    bids_present = Bids.objects.filter(listingid=list_id)
    startingbid = auction_listing.starting_bid
    min_req_bid = minbid(startingbid, bids_present)

    if int(bid_amnt) > int(min_req_bid):
        mybid = Bids(user=request.user, listingid=list_id, bid=bid_amnt)
        mybid.save()
        auction_listing.current_bid = bid_amnt
        auction_listing.save()
        messages.success(request, "Bid placed successfully.")
        return redirect("auctionDetails", list_id)

    messages.warning(request, f"Sorry, {bid_amnt} is less. It should be more than {min_req_bid}$.")
    return redirect("auctionDetails", list_id)


# shows comments made by different user and allows to add comments
@login_required(login_url='login')
def allcomments(request):
    comment = request.GET["comment"]
    username = request.user.username
    list_id = request.GET["listid"]
    new_comment = Comments(user=username, comment=comment, listingid=list_id)
    new_comment.save()
    return listingpage(request, list_id)


# shows message abt winner when bid is closed
def win_ner(request):
    bid_id = request.GET.get("listid")
    bids_present = Bids.objects.filter(listingid=bid_id)
    biddesc = AuctionList.objects.get(pk=bid_id, active_bool=True)
    max_bid = minbid(biddesc.starting_bid, bids_present)

    try:
        # Get the winning bid and user
        winner_object = Bids.objects.get(bid=max_bid, listingid=bid_id)
        winner_user = winner_object.user

        # Check if the winner is the owner of the auction
        if winner_user == biddesc.user:
            messages.error(request, "The auction owner cannot win their own bid.")
            return redirect("myAuction")

        # If valid, save the winner details
        win = Winner(bid_win_list=biddesc, user=winner_user)
        winners_name = winner_user.username

    except ObjectDoesNotExist:
        # Handle the case where no bid was found
        # This should not happen if `max_bid` is properly computed
        messages.error(request, "No valid bid found.")
        return redirect("myAuction")

    # Deactivate the auction
    biddesc.active_bool = False
    biddesc.save()

    # Save winner details
    win.save()
    messages.success(request, f"{winners_name} won {win.bid_win_list.title}.")
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

    user_auctions = AuctionList.objects.filter(id__in=[bid.listingid for bid in userBids])

    for auction in user_auctions:
        first_image = AuctionImage.objects.filter(auction=auction).first()
        if first_image:
            auction.image_url = request.build_absolute_uri(first_image.image_url.url)
        else:
            auction.image_url = None

        auction.total_bids = Bids.objects.filter(listingid=auction.id).count()

    user = request.user

    profile_picture_url = None
    if user.profile_picture:
        profile_picture_url = request.build_absolute_uri(user.profile_picture.url)

    return render(request, "my-bid.html", {
        'email': user.email,
        'name': f"{user.first_name} {user.last_name}",
        'profile_picture': profile_picture_url,
        "userBids": user_auctions
    })


@login_required(login_url='login')
def user_profile(request):
    user = request.user

    profile_picture_url = None
    if user.profile_picture:
        profile_picture_url = request.build_absolute_uri(user.profile_picture.url)

    context = {
        'username': user.username,
        'email': user.email,
        'name': f"{user.first_name} {user.last_name}",
        'profile_picture': profile_picture_url,
    }
    return render(request, "profile.html", context)


@login_required(login_url='login')
def user_win_bids(request):
    win_lists = Winner.objects.filter(user=request.user)

    auctions = []
    for win in win_lists:
        auction = AuctionList.objects.get(id=win.bid_win_list.pk)

        first_image = AuctionImage.objects.filter(auction=auction).first()
        image_url = request.build_absolute_uri(first_image.image_url.url) if first_image else None

        auctions.append({
            'id': auction.id,
            'title': auction.title,
            'starting_bid': auction.starting_bid,
            'current_bid': auction.current_bid,
            'buy_now_price': auction.buy_now_price,
            'expire_date': auction.expire_date,
            'image_url': image_url
        })

    user = request.user
    profile_picture_url = None
    if hasattr(user, 'profile_picture') and user.profile_picture:
        profile_picture_url = request.build_absolute_uri(user.profile_picture.url)

    return render(request, "winning-bids.html", {
        'email': user.email,
        'name': f"{user.first_name} {user.last_name}",
        'profile_picture': profile_picture_url,
        'auctions': auctions
    })


@login_required(login_url='login')
def myauction(request):
    auctions = AuctionList.objects.filter(user=request.user)

    auction_list = []
    for auction in auctions:
        first_image = AuctionImage.objects.filter(auction=auction).first()
        first_image_url = request.build_absolute_uri(first_image.image_url.url) if first_image else None

        auction_list.append({
            'id': auction.id,
            'title': auction.title,
            'starting_bid': auction.starting_bid,
            'current_bid': auction.current_bid,
            'buy_now_price': auction.buy_now_price,
            'bid_watch_list': auction.bid_watch_list,
            'expire_date': auction.expire_date,
            'image_url': first_image_url,
            'active_status': auction.active_bool
        })

    user = request.user
    profile_picture_url = None
    if hasattr(user, 'profile_picture') and user.profile_picture:
        profile_picture_url = request.build_absolute_uri(user.profile_picture.url)

    # Pagination
    paginator = Paginator(auction_list, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    total_auctions = paginator.count

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
        return redirect('update', auction_id=auction_id)

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
