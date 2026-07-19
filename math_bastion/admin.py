from django.contrib import admin

from .models import GemProduct, HighScore, PlayerWallet, Purchase


@admin.register(HighScore)
class HighScoreAdmin(admin.ModelAdmin):
    list_display = ('name', 'score', 'era_reached', 'waves_cleared', 'victory', 'created_at')
    list_filter = ('victory',)
    search_fields = ('name',)
    ordering = ('-score',)


@admin.register(GemProduct)
class GemProductAdmin(admin.ModelAdmin):
    list_display = ('sku', 'name', 'gems', 'bonus_gems', 'price_cents', 'active', 'sort_order')
    list_editable = ('active', 'sort_order')


@admin.register(PlayerWallet)
class PlayerWalletAdmin(admin.ModelAdmin):
    list_display = ('device_key', 'gems', 'lifetime_gems_purchased', 'created_at', 'updated_at')
    readonly_fields = ('device_key',)


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('token', 'product', 'status', 'provider', 'price_cents', 'gems_granted', 'created_at')
    list_filter = ('status', 'provider')
    readonly_fields = ('token', 'wallet', 'product', 'price_cents')
