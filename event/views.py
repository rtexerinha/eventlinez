from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect


# from event.forms import CategoryForm, EventForm
from event.forms import NewEvent
from event.models import Event
from order.models import Order


def order_promoter(request):
    # TODO: Verifica possibilidade de simplificar código sobre login
    if not request.user.is_authenticated:
        return redirect('signin_promoter')
    else:
        promoter = request.user.promoter
        orders = Order.objects.filter(orderitem__event__promoter=promoter)
        return render(request, 'orders_promoter.html', {'order_details': orders})


@login_required
def events_promoter(request):
    if request.user.is_authenticated:
        promoter = request.user.promoter.id
        events = Event.objects.filter(promoter=promoter)
        return render(request, 'events_promoter.html', {'events': events})
    else:
        return render(request, 'accounts/signin_customer.html')


def new_events(request):
    form = NewEvent(request.POST or None)
    promoter = request.user.promoter.id
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('events_promoter')
    return render(request, 'new_event.html', {'form': form, 'promoter': promoter})


'''
def new_events(request):
    CategoryInlineFormSet = inlineformset_factory(Category, Event, form=CategoryForm)
    if request.method == 'POST':
        FormEvent = EventForm(request.POST)
        if FormEvent.is_valid():
            new_event = FormEvent.save()
            categoryInlineFormSet = CategoryInlineFormSet(request.POST, request.FILES, instance=new_event)

            if categoryInlineFormSet.is_valid():
                FormEvent.save()
                return HttpResponseRedirect(reverse('shop:index'))
    else:
        categoryInlineFormSet = CategoryInlineFormSet()
        FormEvent = EventForm()
    return render(request, 'new_event.html', {'categoryInlineFormSet': categoryInlineFormSet,
                                              'FormEvent': FormEvent})
'''