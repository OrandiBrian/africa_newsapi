# --- CONSTANTS ---
ITEMS_PER_PAGE = 10

# --- EXTENSIVE DATA SOURCES ---
FEEDS_BY_REGION = {
    "Pan-African & Tech": {
        "The Africa Report": "https://www.theafricareport.com/feed/",
        "BBC News Africa": "https://feeds.bbci.co.uk/news/world/africa/rss.xml",
        "Anadolu Agency (Africa)": "https://www.aa.com.tr/en/rss/default?cat=africa",
        "TechCabal": "https://techcabal.com/feed/",
        "Buzzroom": "https://buzzcentral.co.ke/feed/",
        "The Guardian": "https://www.theguardian.com/world/africa/rss",
    },
    "Sahel (English)": {
        "HumAngle": "https://humanglemedia.com/feed/",
        "New Humanitarian": "https://www.thenewhumanitarian.org/rss/africa.xml",
        "Voice of America": "https://www.voanews.com/api/zgbpvevmoq"
    },
    "East Africa": {
        "Daily Nation (KE)": "https://nation.africa/service/rss/kenya",
        "East African": "https://www.theeastafrican.co.ke/service/rss/news",
        "Monitor (UG)": "https://www.monitor.co.ug/service/rss/uganda",
        "New Times (RW)": "https://www.newtimes.co.rw/rss",
        "AllAfrica (East)": "https://allafrica.com/tools/headlines/rdf/eastafrica/headlines.rdf"
    },
    "West Africa": {
        "Punch (NG)": "https://punchng.com/feed/",
        "Vanguard (NG)": "https://www.vanguardngr.com/feed/",
        "MyJoyOnline (GH)": "https://www.myjoyonline.com/feed/",
        "AllAfrica (West)": "https://allafrica.com/tools/headlines/rdf/westafrica/headlines.rdf"
    },
    "Southern Africa": {
        "News24 (ZA)": "https://feeds.news24.com/articles/news24/TopStories/rss",
        "Mail & Guardian": "https://mg.co.za/feed/",
        "The Herald (ZW)": "https://www.herald.co.zw/feed/",
        "AllAfrica (South)": "https://allafrica.com/tools/headlines/rdf/southernafrica/headlines.rdf"
    },
    "North Africa": {
        "Ahram Online (EG)": "https://english.ahram.org.eg/News/RSS/1.aspx",
        "Morocco World": "https://www.moroccoworldnews.com/feed",
        "AllAfrica (North)": "https://allafrica.com/tools/headlines/rdf/northafrica/headlines.rdf"
    },
    "Central Africa": {
        "AllAfrica (Central)": "https://allafrica.com/tools/headlines/rdf/centralafrica/headlines.rdf"
    }
}

# Flatten sources for Favorites
ALL_SOURCES_FLAT = {}
for region, feeds in FEEDS_BY_REGION.items():
    for name, url in feeds.items():
        ALL_SOURCES_FLAT[name] = url

AFRICAN_COUNTRIES = sorted([
    "Algeria", "Angola", "Benin", "Botswana", "Burkina Faso", "Burundi", 
    "Cabo Verde", "Cameroon", "Central African Republic", "Chad", "Comoros", 
    "Democratic Republic of the Congo", "Republic of the Congo", "Cote d'Ivoire", 
    "Djibouti", "Egypt", "Equatorial Guinea", "Eritrea", "Eswatini", "Ethiopia", 
    "Gabon", "Gambia", "Ghana", "Guinea", "Guinea-Bissau", "Kenya", "Lesotho", 
    "Liberia", "Libya", "Madagascar", "Malawi", "Mali", "Mauritania", "Mauritius", 
    "Morocco", "Mozambique", "Namibia", "Niger", "Nigeria", "Rwanda", 
    "Sao Tome and Principe", "Senegal", "Seychelles", "Sierra Leone", "Somalia", 
    "South Africa", "South Sudan", "Sudan", "Tanzania", "Togo", "Tunisia", 
    "Uganda", "Zambia", "Zimbabwe"
])
