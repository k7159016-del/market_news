import streamlit as st
import requests
import xml.etree.ElementTree as ET
import re
import html
from datetime import datetime
from email.utils import parsedate_to_datetime


# ============================================================
# FEEDS
# ============================================================

MARKET_FEEDS = {
    "CNBC TV18": "https://www.cnbctv18.com/commonfeeds/v1/cne/rss/market.xml",
    "ET Now": "https://www.etnownews.com/feeds/gns-etn-markets.xml",
    "LiveMint": "https://www.livemint.com/rss/markets",
    "Investment Guru India": "https://investmentguruindia.com/RSS/Stock-News",
    "HBLine": "https://www.thehindubusinessline.com/markets/stock-markets/feeder/default.rss",
}

LATEST_FEEDS = {
    "CNBC TV18": "https://www.cnbctv18.com/commonfeeds/v1/cne/rss/latest.xml",
    "ET Now": "https://www.etnownews.com/feeds/gns-etn-latest.xml",
}


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Market News Dashboard",
    page_icon="📰",
    layout="wide"
)


# ============================================================
# CSS
# ============================================================

st.markdown("""
<style>

.block-container {
    max-width: 1250px;
    padding-top: 1.5rem;
}

.main-title {
    font-size: 34px;
    font-weight: 800;
    margin-bottom: 2px;
}

.subtitle {
    color: #777;
    font-size: 14px;
    margin-bottom: 25px;
}

.section-title {
    font-size: 27px;
    font-weight: 800;
    margin-top: 10px;
    margin-bottom: 5px;
}

.section-line {
    border-bottom: 3px solid #d71920;
    margin-bottom: 25px;
}

.article-title {
    font-size: 21px;
    font-weight: 700;
    line-height: 1.35;
    margin-bottom: 7px;
}

.article-source {
    font-size: 12px;
    font-weight: 700;
    margin-bottom: 3px;
}

.article-date {
    color: #777;
    font-size: 13px;
    margin-bottom: 10px;
}

.article-description {
    color: #555;
    font-size: 14px;
    line-height: 1.5;
    margin-bottom: 12px;
}

.article-divider {
    border-bottom: 1px solid #e5e5e5;
    margin: 25px 0;
}

div[data-testid="stImage"] img {
    border-radius: 8px;
}

button[data-baseweb="tab"] {
    font-size: 16px;
    font-weight: 600;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# DATE PARSER
# ============================================================

def parse_date(value):

    if not value:
        return datetime.min

    value = str(value).strip()

    if not value:
        return datetime.min


    # --------------------------------------------------------
    # Investment Guru India
    #
    # Example:
    # 2026-08-12 05:37:09 pm
    # --------------------------------------------------------

    try:

        return datetime.strptime(
            value,
            "%Y-%m-%d %I:%M:%S %p"
        )

    except Exception:
        pass


    # --------------------------------------------------------
    # Investment Guru India possible variant
    #
    # 2026-08-12 05:37 pm
    # --------------------------------------------------------

    try:

        return datetime.strptime(
            value,
            "%Y-%m-%d %I:%M %p"
        )

    except Exception:
        pass


    # --------------------------------------------------------
    # RFC 822 / Standard RSS
    #
    # Wed, 12 Aug 2026 14:35:00 +0530
    # --------------------------------------------------------

    try:

        dt = parsedate_to_datetime(
            value
        )

        if dt.tzinfo is not None:

            dt = dt.astimezone().replace(
                tzinfo=None
            )

        return dt

    except Exception:
        pass


    # --------------------------------------------------------
    # ISO 8601
    # --------------------------------------------------------

    try:

        iso_value = value.replace(
            "Z",
            "+00:00"
        )

        dt = datetime.fromisoformat(
            iso_value
        )

        if dt.tzinfo is not None:

            dt = dt.astimezone().replace(
                tzinfo=None
            )

        return dt

    except Exception:
        pass


    # --------------------------------------------------------
    # Other common formats
    # --------------------------------------------------------

    formats = [

        "%Y-%m-%d %H:%M:%S",

        "%Y-%m-%d %H:%M",

        "%Y-%m-%dT%H:%M:%S",

        "%Y-%m-%dT%H:%M:%S.%f",

        "%Y-%m-%dT%H:%M:%S%z",

        "%d-%m-%Y %H:%M:%S",

        "%d-%m-%Y %H:%M",

        "%d/%m/%Y %H:%M:%S",

        "%d/%m/%Y %H:%M",

        "%d %b %Y %H:%M:%S",

        "%d %b %Y %H:%M",

        "%d %B %Y %H:%M:%S",

        "%d %B %Y %H:%M",

        "%a, %d %b %Y %H:%M:%S",

        "%a, %d %b %Y %H:%M",

    ]


    for fmt in formats:

        try:

            return datetime.strptime(
                value,
                fmt
            )

        except Exception:
            continue


    return datetime.min


# ============================================================
# FORMAT DATE
# ============================================================

def format_date(dt):

    if dt == datetime.min:

        return "Date unavailable"

    return dt.strftime(
        "%d %b %Y • %I:%M %p"
    )


# ============================================================
# CLEAN HTML
# ============================================================

def clean_html(text):

    if not text:
        return ""

    text = html.unescape(
        text
    )

    text = re.sub(
        r"<[^>]+>",
        "",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# GET XML TEXT
# ============================================================

def get_text(
    element,
    tag
):

    child = element.find(
        tag
    )

    if child is None:

        return ""

    if child.text is None:

        return ""

    return child.text.strip()


# ============================================================
# FIND ARTICLE DATE
# ============================================================

def find_article_date(
    item
):

    # --------------------------------------------------------
    # Standard RSS fields
    # --------------------------------------------------------

    fields = [

        "pubDate",

        "published",

        "updated",

        "date",

        "created",

    ]


    for field in fields:

        value = get_text(
            item,
            field
        )

        if value:

            parsed = parse_date(
                value
            )

            if parsed != datetime.min:

                return parsed


    # --------------------------------------------------------
    # Namespaced fields
    #
    # dc:date
    # atom:updated
    # etc.
    # --------------------------------------------------------

    for child in item:

        tag = child.tag.lower()


        if any(
            keyword in tag
            for keyword in [
                "date",
                "published",
                "updated",
                "created",
                "pubdate"
            ]
        ):

            if child.text:

                value = child.text.strip()


                parsed = parse_date(
                    value
                )


                if parsed != datetime.min:

                    return parsed


    return datetime.min


# ============================================================
# FIND IMAGE
# ============================================================

def find_image(
    item
):

    # --------------------------------------------------------
    # Investment Guru India:
    #
    # <image>https://...</image>
    # --------------------------------------------------------

    image_element = item.find(
        "image"
    )

    if image_element is not None:

        if image_element.text:

            url = image_element.text.strip()

            if url:

                return url


    # --------------------------------------------------------
    # media:content / media:thumbnail
    # --------------------------------------------------------

    for child in item:

        tag = child.tag.lower()


        if (
            "content" in tag
            or "thumbnail" in tag
            or "image" in tag
        ):

            url = child.attrib.get(
                "url",
                ""
            )


            if url:

                return url


    # --------------------------------------------------------
    # enclosure
    # --------------------------------------------------------

    enclosure = item.find(
        "enclosure"
    )


    if enclosure is not None:

        url = enclosure.attrib.get(
            "url",
            ""
        )


        if url:

            return url


    return ""


# ============================================================
# PARSE RSS
# ============================================================

def parse_rss(
    xml_data,
    source
):

    root = ET.fromstring(
        xml_data
    )

    articles = []


    items = root.findall(
        ".//item"
    )


    for item in items:

        # ----------------------------------------------------
        # TITLE
        # ----------------------------------------------------

        title = get_text(
            item,
            "title"
        )


        if not title:

            continue


        # ----------------------------------------------------
        # LINK
        # ----------------------------------------------------

        link = get_text(
            item,
            "link"
        )


        # ----------------------------------------------------
        # DESCRIPTION
        # ----------------------------------------------------

        description = get_text(
            item,
            "description"
        )


        description = clean_html(
            description
        )


        # ----------------------------------------------------
        # DATE
        # ----------------------------------------------------

        article_datetime = (
            find_article_date(
                item
            )
        )


        # ----------------------------------------------------
        # IMAGE
        # ----------------------------------------------------

        image = find_image(
            item
        )


        # ----------------------------------------------------
        # ARTICLE OBJECT
        # ----------------------------------------------------

        article = {

            "source": source,

            "title": clean_html(
                title
            ),

            "link": link,

            "description": description,

            "image": image,

            "datetime": article_datetime,

        }


        articles.append(
            article
        )


    return articles


# ============================================================
# FETCH ONE FEED
# ============================================================

@st.cache_data(ttl=300)
def fetch_feed(
    url,
    source
):

    headers = {

        "User-Agent":
            "Mozilla/5.0 "
            "(Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/138.0 Safari/537.36",

        "Accept":
            "application/rss+xml,"
            "application/xml,"
            "text/xml,"
            "*/*",

        "Referer":
            "https://www.google.com/",
    }


    response = requests.get(
        url,
        headers=headers,
        timeout=30
    )


    response.raise_for_status()


    return parse_rss(
        response.content,
        source
    )


# ============================================================
# FETCH ALL SOURCES
# ============================================================

def fetch_sources(
    feeds
):

    articles = []

    errors = []


    for source, url in feeds.items():

        try:

            source_articles = fetch_feed(
                url,
                source
            )


            articles.extend(
                source_articles
            )


        except Exception as e:

            errors.append(
                f"{source}: {str(e)}"
            )


    return (
        articles,
        errors
    )


# ============================================================
# DEDUPLICATION
# ============================================================

def deduplicate(
    articles
):

    seen = set()

    result = []


    for article in articles:

        link = article.get(
            "link",
            ""
        ).strip().lower()


        title = article.get(
            "title",
            ""
        ).strip().lower()


        if link:

            unique_key = link

        else:

            unique_key = title


        if not unique_key:

            continue


        if unique_key in seen:

            continue


        seen.add(
            unique_key
        )


        result.append(
            article
        )


    return result


# ============================================================
# SORT
# ============================================================

def sort_articles(
    articles
):

    return sorted(
        articles,
        key=lambda x: x.get(
            "datetime",
            datetime.min
        ),
        reverse=True
    )


# ============================================================
# SEARCH
# ============================================================

def apply_search(
    articles,
    search
):

    if not search:

        return articles


    search = search.lower().strip()


    return [

        article

        for article in articles

        if (
            search
            in article.get(
                "title",
                ""
            ).lower()

            or

            search
            in article.get(
                "description",
                ""
            ).lower()
        )

    ]


# ============================================================
# DISPLAY ARTICLE
# ============================================================

def display_article(
    article
):

    title = article.get(
        "title",
        "Untitled"
    )


    link = article.get(
        "link",
        ""
    )


    description = article.get(
        "description",
        ""
    )


    image = article.get(
        "image",
        ""
    )


    source = article.get(
        "source",
        ""
    )


    article_datetime = article.get(
        "datetime",
        datetime.min
    )


    # --------------------------------------------------------
    # Description length
    # --------------------------------------------------------

    if len(description) > 400:

        description = (
            description[:400]
            + "..."
        )


    # --------------------------------------------------------
    # Columns
    # --------------------------------------------------------

    image_col, content_col = st.columns(
        [1.2, 3],
        gap="large"
    )


    # --------------------------------------------------------
    # IMAGE
    # --------------------------------------------------------

    with image_col:

        if image:

            try:

                st.image(
                    image,
                    use_container_width=True
                )

            except Exception:

                st.write("📰")

        else:

            st.write("📰")


    # --------------------------------------------------------
    # CONTENT
    # --------------------------------------------------------

    with content_col:

        st.markdown(
            f"""
            <div class="article-source">
                {source}
            </div>
            """,
            unsafe_allow_html=True
        )


        st.markdown(
            f"""
            <div class="article-title">
                {title}
            </div>
            """,
            unsafe_allow_html=True
        )


        st.markdown(
            f"""
            <div class="article-date">
                🕒 {format_date(article_datetime)}
            </div>
            """,
            unsafe_allow_html=True
        )


        if description:

            st.markdown(
                f"""
                <div class="article-description">
                    {description}
                </div>
                """,
                unsafe_allow_html=True
            )


        if link:

            st.link_button(
                "Read Full Story →",
                link
            )


    st.markdown(
        '<div class="article-divider"></div>',
        unsafe_allow_html=True
    )


# ============================================================
# LOAD FEEDS
# ============================================================

market_articles, market_errors = (
    fetch_sources(
        MARKET_FEEDS
    )
)


latest_articles, latest_errors = (
    fetch_sources(
        LATEST_FEEDS
    )
)


# ============================================================
# DEDUPLICATE
# ============================================================

market_articles = deduplicate(
    market_articles
)


latest_articles = deduplicate(
    latest_articles
)


# ============================================================
# SORT NEWEST → OLDEST
# ============================================================

market_articles = sort_articles(
    market_articles
)


latest_articles = sort_articles(
    latest_articles
)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <div class="main-title">
        📰 Market News Dashboard
    </div>
    """,
    unsafe_allow_html=True
)


st.markdown(
    """
    <div class="subtitle">
        CNBC TV18 • ET Now • LiveMint • Investment Guru India
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header(
        "🔎 Filters"
    )


    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    search = st.text_input(
        "Search news",
        placeholder="e.g. Nifty, RBI, Reliance..."
    )


    st.divider()


    # --------------------------------------------------------
    # MARKET SOURCE FILTER
    # --------------------------------------------------------

    st.subheader(
        "📈 Market Sources"
    )


    selected_market_sources = st.multiselect(
        "Show sources",
        options=list(
            MARKET_FEEDS.keys()
        ),
        default=list(
            MARKET_FEEDS.keys()
        ),
        key="market_filter"
    )


    st.divider()


    # --------------------------------------------------------
    # LATEST SOURCE FILTER
    # --------------------------------------------------------

    st.subheader(
        "🔥 Latest Sources"
    )


    selected_latest_sources = st.multiselect(
        "Show sources",
        options=list(
            LATEST_FEEDS.keys()
        ),
        default=list(
            LATEST_FEEDS.keys()
        ),
        key="latest_filter"
    )


    st.divider()


    # --------------------------------------------------------
    # REFRESH
    # --------------------------------------------------------

    if st.button(
        "🔄 Refresh News",
        use_container_width=True
    ):

        st.cache_data.clear()

        st.rerun()


    st.caption(
        "Feeds automatically refresh every 5 minutes."
    )


# ============================================================
# FILTER MARKET
# ============================================================

filtered_market = [

    article

    for article in market_articles

    if article.get(
        "source"
    ) in selected_market_sources

]


# ============================================================
# FILTER LATEST
# ============================================================

filtered_latest = [

    article

    for article in latest_articles

    if article.get(
        "source"
    ) in selected_latest_sources

]


# ============================================================
# SEARCH
# ============================================================

filtered_market = apply_search(
    filtered_market,
    search
)


filtered_latest = apply_search(
    filtered_latest,
    search
)


# ============================================================
# SORT AGAIN
# ============================================================

filtered_market = sort_articles(
    filtered_market
)


filtered_latest = sort_articles(
    filtered_latest
)


# ============================================================
# TABS
# ============================================================

market_tab, latest_tab = st.tabs(
    [
        f"📈 Market ({len(filtered_market)})",
        f"🔥 Latest ({len(filtered_latest)})"
    ]
)


# ============================================================
# MARKET TAB
# ============================================================

with market_tab:

    st.markdown(
        """
        <div class="section-title">
            📈 Market News
        </div>
        """,
        unsafe_allow_html=True
    )


    st.markdown(
        '<div class="section-line"></div>',
        unsafe_allow_html=True
    )


    if filtered_market:

        # ----------------------------------------------------
        # SOURCE COUNTS
        # ----------------------------------------------------

        source_counts = {}

        for article in filtered_market:

            source = article.get(
                "source",
                "Unknown"
            )

            source_counts[source] = (
                source_counts.get(
                    source,
                    0
                ) + 1
            )


        cols = st.columns(
            len(source_counts)
        )


        for col, (source, count) in zip(
            cols,
            source_counts.items()
        ):

            col.metric(
                source,
                count
            )


        st.divider()


        # ----------------------------------------------------
        # ARTICLES
        # ----------------------------------------------------

        for article in filtered_market:

            display_article(
                article
            )


    else:

        st.info(
            "No market news found."
        )


    # --------------------------------------------------------
    # ERRORS
    # --------------------------------------------------------

    if market_errors:

        with st.expander(
            "⚠️ Feed status"
        ):

            for error in market_errors:

                st.warning(
                    error
                )


# ============================================================
# LATEST TAB
# ============================================================

with latest_tab:

    st.markdown(
        """
        <div class="section-title">
            🔥 Latest News
        </div>
        """,
        unsafe_allow_html=True
    )


    st.markdown(
        '<div class="section-line"></div>',
        unsafe_allow_html=True
    )


    if filtered_latest:

        # ----------------------------------------------------
        # SOURCE COUNTS
        # ----------------------------------------------------

        source_counts = {}

        for article in filtered_latest:

            source = article.get(
                "source",
                "Unknown"
            )

            source_counts[source] = (
                source_counts.get(
                    source,
                    0
                ) + 1
            )


        cols = st.columns(
            len(source_counts)
        )


        for col, (source, count) in zip(
            cols,
            source_counts.items()
        ):

            col.metric(
                source,
                count
            )


        st.divider()


        # ----------------------------------------------------
        # ARTICLES
        # ----------------------------------------------------

        for article in filtered_latest:

            display_article(
                article
            )


    else:

        st.info(
            "No latest news found."
        )


    # --------------------------------------------------------
    # ERRORS
    # --------------------------------------------------------

    if latest_errors:

        with st.expander(
            "⚠️ Feed status"
        ):

            for error in latest_errors:

                st.warning(
                    error
                )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Sources: CNBC TV18 • ET Now • LiveMint • "
    "Investment Guru India"
)