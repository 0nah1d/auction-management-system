from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.db.models import Count, Max, Min
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from .models import *
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.core.mail import send_mail
from .forms import CustomUserCreationForm
from django.contrib.auth.forms import AuthenticationForm
from django.utils.timezone import now, make_aware, get_default_timezone


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


def index(request):
    def add_full_image_url(auction_list):
        for auction in auction_list:
            if auction.image_url:
                auction.image_url = request.build_absolute_uri(auction.image_url.url)
        return auction_list

    top_three_products = AuctionList.objects.filter(active_bool=True).order_by('-buy_now_price')[:3]
    watch_cat_products = AuctionList.objects.filter(active_bool=True, categories__slug='watch')[:3]

    top_three_products = add_full_image_url(top_three_products)
    watch_cat_products = add_full_image_url(watch_cat_products)

    context = {
        'header_bg': True,
        'top_three_products': top_three_products,
        'watch_cat_products': watch_cat_products,
    }
    return render(request, "auctions/index.html", context)


def auction_list(request):
    # Get the search query from the URL parameter
    search_query = request.GET.get('q', '')
    selected_category = request.GET.get('filter-by', 'all')

    # Filter auctions based on the search query
    auctions = AuctionList.objects.filter(active_bool=True)
    if search_query:
        auctions = auctions.filter(Q(title__icontains=search_query))

    if selected_category != 'all':
        auctions = auctions.filter(categories__title=selected_category)

    paginator = Paginator(auctions, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    total_auctions = paginator.count

    # Add full image URL to each auction
    for auction in page_obj:
        if auction.image_url:
            auction.image_url = request.build_absolute_uri(auction.image_url.url)

    # Category
    categories = Category.objects.all()
    return render(request, "auctions/list.html", {
        'auctions': page_obj,
        'categories': categories,
        'selected_category': selected_category,
        'total_auctions': total_auctions
    })


def auction_details(request, bidid):
    biddesc = AuctionList.objects.get(pk=bidid, active_bool=True)
    # Adding full image URL
    if biddesc.image_url:
        biddesc.image_url = request.build_absolute_uri(biddesc.image_url.url)

    bids_present = Bids.objects.filter(listingid=bidid)
    total_bids = Bids.objects.filter(listingid=bidid)
    total_bidders = Bids.objects.filter(listingid=bidid).values('user').annotate(total_bids=Count('user'))

    return render(request, "auctions/details.html", {
        "list": biddesc,
        "comments": Comments.objects.filter(listingid=bidid),
        "present_bid": minbid(biddesc.starting_bid, bids_present),
        "total_bids": len(total_bids),
        "total_bidders": len(total_bidders),
        "is_owner": biddesc.user == request.user
    })


def contact(request):
    return render(request, "auctions/contact.html")


def myauction(request):
    # Retrieve auctions where request.user is the foreign key user
    auctions = AuctionList.objects.filter(user=request.user, active_bool=True)

    # Pagination
    paginator = Paginator(auctions, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    total_auctions = paginator.count
    return render(request, "auctions/myauction.html", {
        'auctions': page_obj,
        'total_auctions': total_auctions
    })


@login_required(login_url='login')
def create(request):
    if request.method == "POST":
        m = AuctionList()
        m.user = request.user  # Set the user object, not the username
        m.title = request.POST.get("create_title")
        m.desc = request.POST.get("create_desc")
        m.short_desc = request.POST.get("create_short_desc")
        m.starting_bid = request.POST.get("create_initial_bid")
        m.buy_now_price = request.POST.get("create_buy_now_price", 0)
        m.image_url = request.FILES.get("img_url")  # Handle file upload
        m.save()  # Save the auction first to get the instance

        # Handle many-to-many relationships
        categories = request.POST.getlist("category")
        for category_slug in categories:
            category = Category.objects.get(slug=category_slug)
            m.categories.add(category)

        m.save()  # Save changes to the many-to-many relationship

        return redirect("index")

    return render(request, "auctions/create.html", {'categories': Category.objects.all()})


@login_required(login_url='login')
def dashboard(request):
    # print(request.user.username)
    userBids = Bids.objects.filter(user=request.user.username)
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
    bid_id = request.GET["listid"]
    bids_present = Bids.objects.filter(listingid=bid_id)
    biddesc = AuctionList.objects.get(pk=bid_id, active_bool=True)
    max_bid = minbid(biddesc.starting_bid, bids_present)
    try:
        # checks if anyone other than list_owner win the bid
        winner_object = Bids.objects.get(bid=max_bid, listingid=bid_id)
        winner_obj = AuctionList.objects.get(id=bid_id)
        win = Winner(bid_win_list=winner_obj, user=winner_object.user)
        winners_name = winner_object.user

    except:
        # if no-one placed a bid, and if bid is closed by list_owner, owner wins the bid
        winner_obj = AuctionList.objects.get(starting_bid=max_bid, id=bid_id)
        win = Winner(bid_win_list=winner_obj, user=winner_obj.user)
        winners_name = winner_obj.user

    # Check Django Documentary for Updating attributes based on existing fields.
    biddesc.active_bool = False
    biddesc.save()

    # saving winner details
    win.save()
    messages.success(request, f"{winners_name} won {win.bid_win_list.title}.")
    return redirect("index")


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
    userBids = Bids.objects.filter(user=request.user.username)
    user_auctions = AuctionList.objects.filter(id__in=[bid.listingid for bid in userBids])

    total_bids = 0
    for auction in user_auctions:
        auction.image_url = request.build_absolute_uri(auction.image_url.url)
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
    # Retrieve the winner objects for the logged-in user
    win_lists = Winner.objects.filter(user=request.user)

    # Get the associated auction lists
    auctions = []
    for win in win_lists:
        auction = AuctionList.objects.get(id=win.bid_win_list.pk)
        if auction.image_url:
            auction.image_url = request.build_absolute_uri(auction.image_url.url)
        auctions.append({
            'winner': win,
            'auction': auction
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
