"""
Fix all remaining .get() calls on MergerResult objects
This script identifies and provides fixes for all merger_result.get() calls
"""

print("""
REMAINING MERGER_RESULT .GET() CALLS TO FIX:

1. _create_ppa_tab method - line ~1170:
   - merger_result.get('purchase_price')
   - merger_result.get('tangible_assets', ...)
   - merger_result.get('identifiable_intangibles', ...)
   - merger_result.get('goodwill', ...)

2. _create_synergies_tab method - line ~1270:
   - merger_result.get('total_synergies')
   - merger_result.get('after_tax_synergies', ...)
   - merger_result.get('revenue_synergies', ...)
   - merger_result.get('cost_synergies', ...)

All of these need to be wrapped in isinstance() checks to handle both
MergerResult objects (use attributes) and dicts (use .get())

THE FIX:
Replace patterns like:
    if merger_result and (hasattr(merger_result, 'attr') or merger_result.get('attr')):
        value = merger_result.get('attr', default)

With:
    if merger_result and (hasattr(merger_result, 'attr') or (isinstance(merger_result, dict) and merger_result.get('attr'))):
        if hasattr(merger_result, 'attr'):
            value = merger_result.attr
        else:
            value = merger_result.get('attr', default)

This allows the code to handle BOTH MergerResult objects AND dictionary representations.
""")
