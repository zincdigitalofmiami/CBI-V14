#!/bin/bash

# SOCIAL MEDIA INTELLIGENCE SCRAPING SCRIPTS
# Production-ready cURL commands for commodity market intelligence
# Execute with: ./production_social_scraper.sh

# Set your API key
export SC_API_KEY="B1TOgQvMVSV6TDglqB8lJ2cirqi2"

# Create output directories
mkdir -p data/{twitter,truth_social,facebook,linkedin,youtube,reddit,tiktok}
mkdir -p logs

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a logs/scraping.log
}

log "Starting social media intelligence collection..."

# ============================================================================
# HIGH-ALPHA SOURCES (1-5 minute polling priority)
# ============================================================================

# TRUMP & EXECUTIVE BRANCH
trump_twitter_handles=(
    "realDonaldTrump"
    "DonaldJTrumpJr" 
    "EricTrump"
    "POTUS"
    "VP"
    "WhiteHouse"
)

policy_handles=(
    "USTreasury"
    "SecYellen"
    "StateDept"
    "CommerceGov"
    "USTR"
    "ICEgov"
    "CBP"
    "DHSgov"
)

china_handles=(
    "CCTVNews"
    "XinhuaNews"
    "PDChina"
    "CGTNOfficial"
    "ChinaDaily"
    "MOFCOMChina"
    "MFA_China"
    "ChinaEmbinUS"
    "GACC_China"
    "cofcointl"
    "sinochem_news"
    "sinograin_china"
)

# Function: Twitter user tweets
scrape_twitter_user() {
    local handle=$1
    local output_file="data/twitter/${handle}_tweets.json"
    
    log "Scraping Twitter user: @$handle"
    
    curl -sS -m 25 --retry 2 -G 'https://api.scrapecreators.com/v1/twitter/user-tweets' \
      -H "x-api-key: $SC_API_KEY" \
      --data-urlencode "handle=$handle" \
      --data-urlencode 'trim=true' \
      -o "$output_file"
    
    if [ $? -eq 0 ]; then
        log "✅ Successfully scraped @$handle"
        # Extract and log tweet count
        tweet_count=$(jq '.tweets | length' "$output_file" 2>/dev/null || echo "0")
        log "   📊 Found $tweet_count tweets"
    else
        log "❌ Failed to scrape @$handle"
    fi
}

# Function: Truth Social posts (requires post URLs)
scrape_truth_social_post() {
    local post_url=$1
    local filename=$(basename "$post_url" | tr '/' '_')
    local output_file="data/truth_social/${filename}.json"
    
    log "Scraping Truth Social post: $post_url"
    
    curl -sS -m 25 --retry 2 -G 'https://api.scrapecreators.com/v1/truthsocial/post' \
      -H "x-api-key: $SC_API_KEY" \
      --data-urlencode "url=$post_url" \
      -o "$output_file"
    
    if [ $? -eq 0 ]; then
        log "✅ Successfully scraped Truth Social post"
    else
        log "❌ Failed to scrape Truth Social post"
    fi
}

# Function: Facebook profile posts - GET ALL POSTS
scrape_facebook_profile() {
    local page_url=$1
    local page_name=$(basename "$page_url")
    local output_file="data/facebook/${page_name}_posts.json"
    local all_posts_file="data/facebook/${page_name}_all_posts.json"
    
    log "Scraping Facebook profile: $page_url"
    
    # Try to get ALL posts with CURSOR-based pagination
    local all_posts=()
    local cursor=""
    local page=1
    local max_pages=100  # Safety limit
    local has_more=true
    
    while [ "$has_more" = true ] && [ $page -le $max_pages ]; do
        local temp_file="data/facebook/${page_name}_page_${page}.json"
        
        log "  Fetching page $page..."
        
        # Build curl command with cursor if available
        local curl_cmd="curl -sS -m 45 --retry 2 -G 'https://api.scrapecreators.com/v1/facebook/profile/posts' \
          -H 'x-api-key: $SC_API_KEY' \
          --data-urlencode 'url=$page_url' \
          --data-urlencode 'count=100'"
        
        if [ -n "$cursor" ]; then
            curl_cmd="$curl_cmd --data-urlencode 'cursor=$cursor'"
        fi
        
        eval "$curl_cmd -o '$temp_file'"
        
        if [ $? -eq 0 ]; then
            local page_posts=$(jq -r '.posts // []' "$temp_file" 2>/dev/null)
            local post_count=$(echo "$page_posts" | jq 'length' 2>/dev/null || echo "0")
            cursor=$(jq -r '.cursor // empty' "$temp_file" 2>/dev/null)
            
            if [ "$post_count" -gt 0 ]; then
                log "    ✅ Page $page: $post_count posts (cursor: ${cursor:0:20}...)"
                all_posts+=("$temp_file")
                
                if [ -z "$cursor" ] || [ "$cursor" = "null" ] || [ "$cursor" = "" ]; then
                    log "    ⚠️  No more cursor - reached end"
                    has_more=false
                else
                    page=$((page + 1))
                    sleep 2  # Rate limiting
                fi
            else
                log "    ⚠️  Page $page: No posts returned"
                has_more=false
                rm -f "$temp_file"
            fi
        else
            log "    ❌ Page $page: Failed"
            has_more=false
            rm -f "$temp_file"
        fi
    done
    
    # Combine all pages
    if [ ${#all_posts[@]} -gt 0 ]; then
        log "  Combining ${#all_posts[@]} pages..."
        jq -s '{posts: [.[] | .posts // [] | .[]]}' "${all_posts[@]}" > "$all_posts_file" 2>/dev/null
        mv "$all_posts_file" "$output_file"
        rm -f "${all_posts[@]}"
        
        local total_posts=$(jq '.posts | length' "$output_file" 2>/dev/null || echo "0")
        log "✅ Successfully scraped Facebook profile: $page_name"
        log "   📊 Total posts collected: $total_posts"
    else
        # Fallback: try single request with max count
        log "  Fallback: Single request with max parameters..."
        curl -sS -m 30 --retry 2 -G 'https://api.scrapecreators.com/v1/facebook/profile/posts' \
          -H "x-api-key: $SC_API_KEY" \
          --data-urlencode "url=$page_url" \
          --data-urlencode "count=1000" \
          --data-urlencode "limit=1000" \
          -o "$output_file"
        
        if [ $? -eq 0 ]; then
            local post_count=$(jq '.posts | length' "$output_file" 2>/dev/null || echo "0")
            log "✅ Successfully scraped Facebook profile: $page_name"
            log "   📊 Found $post_count posts"
        else
            log "❌ Failed to scrape Facebook profile: $page_name"
        fi
    fi
}

# Function: LinkedIn profile
scrape_linkedin_profile() {
    local profile_url=$1
    local profile_name=$(basename "$profile_url")
    local output_file="data/linkedin/${profile_name}_profile.json"
    
    log "Scraping LinkedIn profile: $profile_url"
    
    curl -sS -m 25 --retry 2 -G 'https://api.scrapecreators.com/v1/linkedin/profile' \
      -H "x-api-key: $SC_API_KEY" \
      --data-urlencode "url=$profile_url" \
      -o "$output_file"
    
    if [ $? -eq 0 ]; then
        log "✅ Successfully scraped LinkedIn profile: $profile_name"
    else
        log "❌ Failed to scrape LinkedIn profile: $profile_name"
    fi
}

# Function: YouTube hashtag search
scrape_youtube_hashtag() {
    local hashtag=$1
    local output_file="data/youtube/hashtag_${hashtag}.json"
    
    log "Scraping YouTube hashtag: #$hashtag"
    
    curl -sS -m 25 --retry 2 -G 'https://api.scrapecreators.com/v1/youtube/search/hashtag' \
      -H "x-api-key: $SC_API_KEY" \
      --data-urlencode "hashtag=$hashtag" \
      --data-urlencode 'type=all' \
      -o "$output_file"
    
    if [ $? -eq 0 ]; then
        log "✅ Successfully scraped YouTube hashtag: #$hashtag"
        video_count=$(jq '.videos | length' "$output_file" 2>/dev/null || echo "0")
        log "   📊 Found $video_count videos"
    else
        log "❌ Failed to scrape YouTube hashtag: #$hashtag"
    fi
}

# Function: Reddit search
scrape_reddit_search() {
    local query=$1
    local timeframe=$2
    local output_file="data/reddit/search_$(echo "$query" | tr ' ' '_' | tr '"' '_').json"
    
    log "Scraping Reddit query: $query (timeframe: $timeframe)"
    
    curl -sS -m 25 --retry 2 -G 'https://api.scrapecreators.com/v1/reddit/search' \
      -H "x-api-key: $SC_API_KEY" \
      --data-urlencode "query=$query" \
      --data-urlencode 'sort=new' \
      --data-urlencode "timeframe=$timeframe" \
      --data-urlencode 'trim=true' \
      -o "$output_file"
    
    if [ $? -eq 0 ]; then
        log "✅ Successfully scraped Reddit query: $query"
        post_count=$(jq '.posts | length' "$output_file" 2>/dev/null || echo "0")
        log "   📊 Found $post_count posts"
    else
        log "❌ Failed to scrape Reddit query: $query"
    fi
}

# Function: TikTok profile
scrape_tiktok_profile() {
    local handle=$1
    local output_file="data/tiktok/${handle}_profile.json"
    
    log "Scraping TikTok profile: @$handle"
    
    curl -sS -m 25 --retry 2 -G 'https://api.scrapecreators.com/v1/tiktok/profile' \
      -H "x-api-key: $SC_API_KEY" \
      --data-urlencode "handle=$handle" \
      -o "$output_file"
    
    if [ $? -eq 0 ]; then
        log "✅ Successfully scraped TikTok profile: @$handle"
    else
        log "❌ Failed to scrape TikTok profile: @$handle"
    fi
}

# ============================================================================
# EXECUTION: HIGH-ALPHA TWITTER HANDLES
# ============================================================================

log "🚀 Starting HIGH-ALPHA Twitter scraping..."

# Trump & Executive Branch
for handle in "${trump_twitter_handles[@]}"; do
    scrape_twitter_user "$handle"
    sleep 2  # Rate limiting
done

# Policy handles
for handle in "${policy_handles[@]}"; do
    scrape_twitter_user "$handle"
    sleep 2
done

# China handles
for handle in "${china_handles[@]}"; do
    scrape_twitter_user "$handle"
    sleep 2
done

# ============================================================================
# EXECUTION: CONGRESS & AGRICULTURE
# ============================================================================

congress_handles=(
    "SenateAg"
    "HouseAg" 
    "ChairmanThompson"
    "SenBooker"
    "RepAustin"
    "SenJoniErnst"
    "ChuckGrassley"
    "SenAmyKlobuchar"
    "SenatorFischer"
    "RepFeenstra"
)

log "🏛️ Starting CONGRESS Twitter scraping..."

for handle in "${congress_handles[@]}"; do
    scrape_twitter_user "$handle"
    sleep 3
done

# ============================================================================
# EXECUTION: COMMODITY MAJORS & EXCHANGES
# ============================================================================

commodity_handles=(
    "ADMCorp"
    "BungeGlobal"
    "Cargill"
    "LouisDreyfus"
    "Viterra_Global"
    "CMEGroup"
    "ICE_Markets"
    "nasdaq"
    "CBOTExchange"
    "OilWorld"
    "FCStoneGlobal"
    "Informa_Agri"
)

log "📈 Starting COMMODITY MAJORS Twitter scraping..."

for handle in "${commodity_handles[@]}"; do
    scrape_twitter_user "$handle"
    sleep 3
done

# ============================================================================
# EXECUTION: BRAZIL & ARGENTINA AGRICULTURE
# ============================================================================

brazil_handles=(
    "MinAgricultura"
    "abioveoficial"
    "AprosojaBrasil"
    "conab_oficial"
    "anpbrasil"
    "ubrabio"
    "canalrural"
    "noticiasagri"
    "agrolink"
    "ruralbr"
)

argentina_handles=(
    "CIARA_CEC"
    "ArgentinaGob"
    "BCRAmercados"
    "MAGyPArgentina"
    "INDEC_Argentina"
    "CancelleriaArg"
)

log "🇧🇷 Starting BRAZIL Twitter scraping..."

for handle in "${brazil_handles[@]}"; do
    scrape_twitter_user "$handle"
    sleep 3
done

log "🇦🇷 Starting ARGENTINA Twitter scraping..."

for handle in "${argentina_handles[@]}"; do
    scrape_twitter_user "$handle"
    sleep 3
done

# ============================================================================
# EXECUTION: US AGRICULTURE & FARMERS
# ============================================================================

us_ag_handles=(
    "FarmBureau"
    "NationalCorn"
    "ASA_Soybeans"
    "NOPA_News"
    "NationalGrange"
    "NFUnion"
    "USGrains"
    "USSEC"
    "corn_soydigest"
    "SuccessfulFarm"
    "FarmProgress"
    "AgWeb"
    "dtnpf"
)

log "🚜 Starting US AGRICULTURE Twitter scraping..."

for handle in "${us_ag_handles[@]}"; do
    scrape_twitter_user "$handle"
    sleep 3
done

# ============================================================================
# EXECUTION: BIOFUELS & ENERGY POLICY
# ============================================================================

biofuel_handles=(
    "EPA"
    "EnergyGov"
    "USDA"
    "SecVilsack"
    "CleanFuelsDA"
    "BiodieselNow"
    "EthanolRFA"
    "CARB"
    "EU_Commission"
    "EU_CouncilEU"
    "mpobmalaysia"
    "gapki_id"
    "icopalmoil"
)

log "⚡ Starting BIOFUELS Twitter scraping..."

for handle in "${biofuel_handles[@]}"; do
    scrape_twitter_user "$handle"
    sleep 3
done

# ============================================================================
# EXECUTION: FACEBOOK PROFILES
# ============================================================================

facebook_urls=(
    "https://www.facebook.com/USDA"
    "https://www.facebook.com/EPA"
    "https://www.facebook.com/AmericanSoybeanAssociation"
    "https://www.facebook.com/NationalBiodieselBoard"
    "https://www.facebook.com/CMEGroup"
    "https://www.facebook.com/ADMCorp"
    "https://www.facebook.com/BungeGlobal"
    "https://www.facebook.com/Cargill"
)

log "📘 Starting FACEBOOK scraping..."

for url in "${facebook_urls[@]}"; do
    scrape_facebook_profile "$url"
    sleep 5  # Facebook rate limiting
done

# ============================================================================
# EXECUTION: LINKEDIN PROFILES
# ============================================================================

linkedin_urls=(
    "https://www.linkedin.com/company/usda"
    "https://www.linkedin.com/company/epa"
    "https://www.linkedin.com/company/adm"
    "https://www.linkedin.com/company/bunge"
    "https://www.linkedin.com/company/cargill"
    "https://www.linkedin.com/company/cme-group"
    "https://www.linkedin.com/company/ice"
    "https://www.linkedin.com/company/american-soybean-association"
)

log "💼 Starting LINKEDIN scraping..."

for url in "${linkedin_urls[@]}"; do
    scrape_linkedin_profile "$url"
    sleep 5  # LinkedIn rate limiting
done

# ============================================================================
# EXECUTION: YOUTUBE HASHTAG DISCOVERY
# ============================================================================

youtube_hashtags=(
    "soybeans"
    "soyoil"
    "biodiesel"
    "agriculture"
    "commodities"
    "trade"
    "tariffs"
    "china"
    "brazil"
    "argentina"
    "drought"
    "harvest"
    "farming"
    "RFS"
    "palmoil"
)

log "📺 Starting YOUTUBE hashtag scraping..."

for hashtag in "${youtube_hashtags[@]}"; do
    scrape_youtube_hashtag "$hashtag"
    sleep 4
done

# ============================================================================
# EXECUTION: REDDIT KEYWORD SEARCHES
# ============================================================================

reddit_queries=(
    "soybean oil"
    "palm oil"
    "biodiesel"
    "RFS renewable fuel standard"
    "tariff china trade"
    "brazil harvest soybean"
    "argentina exports agriculture"
    "commodity futures trading"
    "agricultural policy"
    "drought farming weather"
    "USDA report"
    "China imports soybeans"
    "Trump agriculture trade"
    "biofuel mandate"
    "crushing margins"
)

log "🔍 Starting REDDIT search scraping..."

for query in "${reddit_queries[@]}"; do
    scrape_reddit_search "$query" "month"
    sleep 4
done

# ============================================================================
# EXECUTION: TIKTOK PROFILES
# ============================================================================

tiktok_handles=(
    "usda"
    "epa"
    "farmbureau"
    "agriculture"
    "commoditytrader"
    "farmlife"
    "soybeanfarmer"
    "cornfarmer"
)

log "🎵 Starting TIKTOK profile scraping..."

for handle in "${tiktok_handles[@]}"; do
    scrape_tiktok_profile "$handle"
    sleep 4
done

# ============================================================================
# EXECUTION: TRUTH SOCIAL (Requires manual post URL collection)
# ============================================================================

# Truth Social post URLs (update these with actual recent post URLs)
truth_social_posts=(
    "https://truthsocial.com/@realDonaldTrump/posts/113143847892847392"
    "https://truthsocial.com/@realDonaldTrump/posts/113142756834523847"
    # Add more recent post URLs as discovered
)

log "🇺🇸 Starting TRUTH SOCIAL scraping..."

for post_url in "${truth_social_posts[@]}"; do
    scrape_truth_social_post "$post_url"
    sleep 3
done

# ============================================================================
# ADVANCED: BULK BACKFILL FOR HIGH-PRIORITY HANDLES
# ============================================================================

log "🔄 Starting BULK BACKFILL for high-priority handles..."

# Create combined high-alpha handle list
high_alpha_handles=(
    "realDonaldTrump" "USTR" "USTreasury" "ICEgov" "GACC_China" 
    "MOFCOMChina" "cofcointl" "sinograin_china" "EPA" "USDA" 
    "SecVilsack" "CFTC" "CMEGroup" "ICE_Markets" "ASA_Soybeans"
)

# Bulk backfill to single NDJSON file
echo "" > data/twitter/bulk_backfill.ndjson

for handle in "${high_alpha_handles[@]}"; do
    log "Bulk backfilling: @$handle"
    
    curl -sS -m 25 --retry 2 -G 'https://api.scrapecreators.com/v1/twitter/user-tweets' \
      -H "x-api-key: $SC_API_KEY" \
      --data-urlencode "handle=$handle" \
      --data-urlencode 'trim=true' \
    | jq -c --arg handle "$handle" '.tweets[]? | . + {scraped_handle: $handle, scraped_timestamp: now}' >> data/twitter/bulk_backfill.ndjson
    
    sleep 2
done

# ============================================================================
# COMPLETION SUMMARY
# ============================================================================

log "🎉 Social media intelligence collection completed!"
log "📊 Generating summary report..."

# Count total files collected
twitter_files=$(find data/twitter -name "*.json" | wc -l)
facebook_files=$(find data/facebook -name "*.json" | wc -l)
linkedin_files=$(find data/linkedin -name "*.json" | wc -l)
youtube_files=$(find data/youtube -name "*.json" | wc -l)
reddit_files=$(find data/reddit -name "*.json" | wc -l)
tiktok_files=$(find data/tiktok -name "*.json" | wc -l)
truth_files=$(find data/truth_social -name "*.json" | wc -l)

log "📈 COLLECTION SUMMARY:"
log "   Twitter files: $twitter_files"
log "   Facebook files: $facebook_files"
log "   LinkedIn files: $linkedin_files"
log "   YouTube files: $youtube_files"
log "   Reddit files: $reddit_files"
log "   TikTok files: $tiktok_files"
log "   Truth Social files: $truth_files"
log "   Total files: $((twitter_files + facebook_files + linkedin_files + youtube_files + reddit_files + tiktok_files + truth_files))"

# Calculate approximate data size
total_size=$(du -sh data/ | cut -f1)
log "   Total data collected: $total_size"

log "✅ All social media intelligence collection completed successfully!"
log "🚀 Ready for BigQuery ingestion and signal processing!"

# Create ingestion manifest
cat > data/ingestion_manifest.json << EOF
{
  "collection_timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "platforms_scraped": [
    "twitter", "facebook", "linkedin", "youtube", "reddit", "tiktok", "truth_social"
  ],
  "file_counts": {
    "twitter": $twitter_files,
    "facebook": $facebook_files,
    "linkedin": $linkedin_files,
    "youtube": $youtube_files,
    "reddit": $reddit_files,
    "tiktok": $tiktok_files,
    "truth_social": $truth_files
  },
  "total_files": $((twitter_files + facebook_files + linkedin_files + youtube_files + reddit_files + tiktok_files + truth_files)),
  "data_directory": "./data/",
  "next_steps": [
    "Upload to Google Cloud Storage",
    "Ingest into BigQuery staging tables", 
    "Run signal processing pipeline",
    "Update forecast models with social sentiment"
  ]
}
EOF

log "📋 Ingestion manifest created: data/ingestion_manifest.json"


