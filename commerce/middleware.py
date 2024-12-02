from django.shortcuts import redirect
from django.urls import reverse

class RedirectAuthenticatedMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        restricted_paths = [
            reverse('login'),
            reverse('register')
        ]

        if request.user.is_authenticated and request.path in restricted_paths:
            return redirect('index')

        response = self.get_response(request)
        return response
