from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from .models import CardSet, Card


class CardSetListView(ListView):
    """List all active card sets."""
    model = CardSet
    template_name = 'card_maker/set_list.html'
    context_object_name = 'sets'
    
    def get_queryset(self):
        return CardSet.objects.filter(is_active=True)


class CardSetDetailView(DetailView):
    """View a card set and its cards."""
    model = CardSet
    template_name = 'card_maker/set_detail.html'
    context_object_name = 'card_set'
    slug_url_kwarg = 'slug'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cards'] = self.object.cards.filter(is_active=True).order_by('order', 'name')
        return context


class CardDetailView(DetailView):
    """View individual card details."""
    model = Card
    template_name = 'card_maker/card_detail.html'
    context_object_name = 'card'
    slug_url_kwarg = 'card_slug'
    
    def get_queryset(self):
        set_slug = self.kwargs.get('set_slug')
        return Card.objects.filter(card_set__slug=set_slug, is_active=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get other cards from the same set
        context['other_cards'] = Card.objects.filter(
            card_set=self.object.card_set,
            is_active=True
        ).exclude(id=self.object.id).order_by('order', 'name')[:6]
        return context


def index(request):
    """Card maker app index page."""
    all_sets = CardSet.objects.filter(is_active=True).order_by('-created_at')
    
    # Get selected set from query parameter or default to first set
    selected_set_slug = request.GET.get('set')
    selected_set = None
    cards = []
    
    if selected_set_slug:
        try:
            selected_set = CardSet.objects.get(slug=selected_set_slug, is_active=True)
            cards = selected_set.cards.filter(is_active=True).order_by('order', 'name')
        except CardSet.DoesNotExist:
            selected_set = None
    elif all_sets.exists():
        # Default to first set if no set is selected
        selected_set = all_sets.first()
        cards = selected_set.cards.filter(is_active=True).order_by('order', 'name')
    
    context = {
        'selected_set': selected_set,
        'cards': cards,
        'all_sets': all_sets,
    }
    return render(request, 'card_maker/index.html', context)
