from .models import UserProfile


def user_profile(request):
    user_profile = None
    if request.user.is_authenticated:
        user_profile, _ = UserProfile.objects.get_or_create(user=request.user)
    return {
        'user_profile': user_profile,
    }
