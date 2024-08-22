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
from django.core.mail import send_mail
from .forms import CustomUserCreationForm
from django.contrib.auth.forms import AuthenticationForm
from django.utils.timezone import now, make_aware, get_default_timezone
from django.core.files.storage import default_storage
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist


def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect(reverse("index"))
        else:
            return render(request, "auctions/register.html", {
                "form": form
            })
    else:
        form = CustomUserCreationForm()
        return render(request, "auctions/register.html", {
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

    return render(request, "auctions/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


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


def index(request):
    def add_full_image_url(auction_list):
        for auction in auction_list:
            first_image = AuctionImage.objects.filter(auction=auction).first()
            if first_image:
                auction.first_image_url = request.build_absolute_uri(first_image.image_url.url)
            else:
                auction.first_image_url = None  # Or set a default image URL if you prefer
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
    return render(request, "auctions/index.html", context)


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
    return render(request, "auctions/list.html", {
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

    return render(request, "auctions/details.html", {
        "list": biddesc,
        "image_urls": image_urls,
        "comments": Comments.objects.filter(listingid=bidid),
        "present_bid": minbid(biddesc.starting_bid, bids_present),
        "total_bids": len(total_bids),
        "total_bidders": len(total_bidders),
        "is_owner": biddesc.user == request.user
    })


def contact(request):
    return render(request, "auctions/contact.html")


@login_required(login_url='login')
def create(request):
    if request.method == "POST":
        # Initialize the auction object
        m = AuctionList(user=request.user)

        # Validate and assign title
        title = request.POST.get("create_title")
        if not title:
            messages.error(request, "Title is required.")
            return render(request, "auctions/create.html", {'categories': Category.objects.all()})
        m.title = title

        # Validate and assign description
        desc = request.POST.get("create_desc")
        if not desc:
            messages.error(request, "Description is required.")
            return render(request, "auctions/create.html", {'categories': Category.objects.all()})
        m.desc = desc

        # Validate and assign starting bid
        starting_bid = request.POST.get("create_initial_bid")
        if not starting_bid or int(starting_bid) <= 0:
            messages.error(request, "Starting bid must be a positive number.")
            return render(request, "auctions/create.html", {'categories': Category.objects.all()})
        m.starting_bid = int(starting_bid)

        buy_now_price = request.POST.get("create_buy_now_price", 0)
        m.buy_now_price = int(buy_now_price)

        # Validate and assign expiration date
        expire_date = request.POST.get("expire_date")
        if not expire_date:
            messages.error(request, "Expiration date is required.")
            return render(request, "auctions/create.html", {'categories': Category.objects.all()})
        m.expire_date = expire_date

        # Save the auction first to get the instance
        m.save()

        # Handle category
        selected_category_slug = request.POST.get("category")

        if selected_category_slug == "new":
            new_category_title = request.POST.get("new_category_title")

            if new_category_title:
                category, created = Category.objects.get_or_create(
                    title=new_category_title,
                    defaults={'slug': new_category_title.lower().replace(' ', '-')}
                )
                m.categories.add(category)
            else:
                messages.error(request, "New category title cannot be empty.")
                return render(request, "auctions/create.html", {'categories': Category.objects.all()})
        else:
            try:
                category = Category.objects.get(slug=selected_category_slug)
                m.categories.add(category)
            except Category.DoesNotExist:
                messages.error(request, f"Category with slug '{selected_category_slug}' does not exist.")
                return render(request, "auctions/create.html", {'categories': Category.objects.all()})

        # Handle image uploads
        images = request.FILES.getlist("img_url")
        for image in images:
            AuctionImage.objects.create(auction=m, image_url=image)

        return redirect("index")

    return render(request, "auctions/create.html", {'categories': Category.objects.all()})


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

    return render(request, "auctions/dashboard.html", {
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

    return render(request, "auctions/details.html", {
        "list": biddesc,
        "comments": Comments.objects.filter(listingid=bidid),
        "present_bid": minbid(biddesc.starting_bid, bids_present),
    })


@login_required(login_url='login')
def watchlistpage(request, username):
    # present_w = watchlist.objects.get(user = "username")
    list_ = Watchlist.objects.filter(user=username)
    return render(request, "auctions/watchlist.html", {
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
        mybid = Bids(user=request.user.username, listingid=list_id, bid=bid_amnt)
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

    return render(request, "auctions/winnings.html", {
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

    return render(request, "auctions/my-bid.html", {
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
    return render(request, "auctions/profile.html", context)


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

    return render(request, "auctions/winning-bids.html", {
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

    return render(request, "auctions/myauction.html", {
        'email': user.email,
        'name': f"{user.first_name} {user.last_name}",
        'profile_picture': profile_picture_url,
        'auctions': page_obj,
        'total_auctions': total_auctions
    })
