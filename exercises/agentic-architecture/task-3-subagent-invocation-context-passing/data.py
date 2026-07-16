"""Mock travel-blog corpus for the exercise (Domain 1.3).

Each blog excerpt carries its own author/blog-name metadata alongside its
text, so dispatch_blog_review_subagent in tools.py can return findings that
keep what a blogger said separate from who said it — see Task Statement
1.3's "structured data formats to separate content from metadata... to
preserve attribution."

The four excerpts intentionally cover different aspects of the same
destination (budget options, a luxury option, safety/logistics, food at
both ends of the price range) so synthesis has real material to combine,
and the later fork into a budget vs. luxury itinerary has genuine signal to
draw from either side.
"""

BLOG_POSTS = {
    "POST-1": {
        "author": "Maria Santos",
        "blog_name": "Wanderlust Diaries",
        "text": (
            "Lisbon's Alfama district is packed with hostels charging under €20 a night, "
            "and the daily special (prato do dia) at neighborhood tascas rarely tops €8 "
            "for a full meal with a drink included."
        ),
    },
    "POST-2": {
        "author": "James Whitfield",
        "blog_name": "Luxury Escapes",
        "text": (
            "The Bairro Alto Hotel's rooftop suites overlook the Tagus river and start "
            "around €450 a night; pair it with a tasting menu at a Michelin-starred spot "
            "like Belcanto for a proper splurge weekend."
        ),
    },
    "POST-3": {
        "author": "Priya Nair",
        "blog_name": "Solo Female Travel",
        "text": (
            "Lisbon is one of the safest capitals in Europe for solo travelers; the "
            "biggest practical issue is the steep, cobblestoned hills, so comfortable "
            "shoes matter more than which neighborhood you pick."
        ),
    },
    "POST-4": {
        "author": "Tom Reyes",
        "blog_name": "Foodie Trails",
        "text": (
            "Time Out Market is a good one-stop sampler of the city's best kitchens at "
            "reasonable prices, but for a splurge, book a table at a fado house in "
            "Alfama for dinner and live music together."
        ),
    },
}
