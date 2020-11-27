from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect


@login_required
def order_promoter(request):
    if not request.user.username:
        return redirect('signin_promoter')
    else:
        return render(request, 'orders_promoter.html')
