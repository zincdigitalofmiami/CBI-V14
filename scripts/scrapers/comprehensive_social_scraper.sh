#!/usr/bin/env bash
# One file. All handles. Minimal fluff. Set SC_API_KEY and run.

set -euo pipefail
: "${SC_API_KEY:?export SC_API_KEY=your_scrapecreators_key}"

sanitize() { echo "$1" | tr '/:@?&= %' '_' | tr -cd '[:alnum:]_.\-'; }

mkdir -p data/{twitter,truth_social,facebook,linkedin,youtube,reddit,tiktok}

##############################################################################
# TWITTER / X — ALL HIGH/MED/LOW PRIORITY HANDLES (from your lists)
##############################################################################
twitter_handles=(
  # Trump/Admin/Exec
  realDonaldTrump DonaldJTrumpJr EricTrump POTUS VP WhiteHouse
  USTreasury SecYellen StateDept CommerceGov USTR ICEgov CBP DHSgov CFTC
  # Congress / Ag
  SenateAg HouseAg ChairmanThompson SenBooker RepAustin SenJoniErnst ChuckGrassley
  SenAmyKlobuchar SenatorFischer RepFeenstra RepCindy_Axne
  # China state & trade
  CCTVNews XinhuaNews PDChina CGTNOfficial ChinaDaily MOFCOMChina MFA_China ChinaEmbinUS
  GACC_China cofcointl sinochem_news sinograin_china
  # Commodity majors & trading
  ADMCorp BungeGlobal Cargill LouisDreyfus Viterra_Global CMEGroup ICE_Markets nasdaq CBOTExchange
  OilWorld FCStoneGlobal Informa_Agri
  # Biofuels & energy policy
  EPA EnergyGov USDA SecVilsack CleanFuelsDA BiodieselNow EthanolRFA CARB EU_Commission EU_CouncilEU
  mpobmalaysia gapki_id icopalmoil
  # Brazil ag & policy
  MinAgricultura abioveoficial AprosojaBrasil conab_oficial anpbrasil ubrabio canalrural noticiasagri agrolink ruralbr
  # Argentina agriculture
  CIARA_CEC ArgentinaGob BCRAmercados MAGyPArgentina INDEC_Argentina CancelleriaArg
  # US ag & farmers
  FarmBureau NationalCorn ASA_Soybeans NOPA_News NationalGrange NFUnion USGrains USSEC
  corn_soydigest SuccessfulFarm FarmProgress AgWeb dtnpf
  # Weather & climate
  NOAA NWS NOAAClimate USDA_NASS WorldWeather AccuWeather WeatherChannel CommodityWX DroughtGov
  # Lobbyists & think tanks
  Heritage AEI BrookingsInst CatoInstitute EconomicPolicy taxpolicyctr CropLifeAmerica bioenergyassoc GrowthEnergy
  # Financial media & analysts
  CNBC BloombergNews Reuters WSJ MarketWatch FT AgFunderNews foodandagtech AgriPulse FarmFutures ProFarmer DowJonesAgNews
)

for h in "${twitter_handles[@]}"; do
  out="data/twitter/$(sanitize "$h")_tweets.json"
  curl -sS --fail-with-body -G 'https://api.scrapecreators.com/v1/twitter/user-tweets' \
    -H "x-api-key: $SC_API_KEY" \
    --data-urlencode "handle=$h" \
    --data-urlencode "trim=true" \
    -o "$out"
done

##############################################################################
# FACEBOOK — key pages (posts)
##############################################################################
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
for url in "${facebook_urls[@]}"; do
  out="data/facebook/$(sanitize "$url")_posts.json"
  curl -sS --fail-with-body -G 'https://api.scrapecreators.com/v1/facebook/profile/posts' \
    -H "x-api-key: $SC_API_KEY" \
    --data-urlencode "url=$url" \
    -o "$out"
done

##############################################################################
# LINKEDIN — company profiles
##############################################################################
linkedin_urls=(
  "https://www.linkedin.com/company/usda"
  "https://www.linkedin.com/company/epa"
  "https://www.linkedin.com/company/adm"
  "https://www.linkedin.com/company/bunge"
  "https://www.linkedin.com/company/cargill"
  "https://www.linkedin.com/company/cme-group"
  "https://www.linkedin.com/company/intercontinental-exchange-inc"
  "https://www.linkedin.com/company/american-soybean-association"
)
for url in "${linkedin_urls[@]}"; do
  out="data/linkedin/$(sanitize "$url")_profile.json"
  curl -sS --fail-with-body -G 'https://api.scrapecreators.com/v1/linkedin/profile' \
    -H "x-api-key: $SC_API_KEY" \
    --data-urlencode "url=$url" \
    -o "$out"
done

##############################################################################
# YOUTUBE — hashtag search (broad discovery)
##############################################################################
yt_hashtags=( soybeans soyoil biodiesel agriculture commodities trade tariffs china brazil argentina drought harvest farming RFS )
for tag in "${yt_hashtags[@]}"; do
  out="data/youtube/hashtag_$(sanitize "$tag").json"
  curl -sS --fail-with-body -G 'https://api.scrapecreators.com/v1/youtube/search/hashtag' \
    -H "x-api-key: $SC_API_KEY" \
    --data-urlencode "hashtag=$tag" \
    --data-urlencode "type=all" \
    -o "$out"
done

##############################################################################
# REDDIT — keyword search (sitewide)
##############################################################################
reddit_queries=(
  "soybean oil" "palm oil" "biodiesel" "RFS renewable fuel standard"
  "tariff china trade" "brazil harvest soybean" "argentina exports agriculture"
  "commodity futures trading" "agricultural policy" "drought farming weather"
  "USDA report" "China imports soybeans" "biofuel mandate" "crushing margins"
)
for q in "${reddit_queries[@]}"; do
  out="data/reddit/search_$(sanitize "$q").json"
  curl -sS --fail-with-body -G 'https://api.scrapecreators.com/v1/reddit/search' \
    -H "x-api-key: $SC_API_KEY" \
    --data-urlencode "query=$q" \
    --data-urlencode "sort=new" \
    --data-urlencode "timeframe=month" \
    --data-urlencode "trim=true" \
    -o "$out"
done

##############################################################################
# TIKTOK — profiles
##############################################################################
tiktok_handles=( usda epa farmbureau agriculture commoditytrader farmlife soybeanfarmer cornharvest cornfarmer )
for h in "${tiktok_handles[@]}"; do
  out="data/tiktok/$(sanitize "$h")_profile.json"
  curl -sS --fail-with-body -G 'https://api.scrapecreators.com/v1/tiktok/profile' \
    -H "x-api-key: $SC_API_KEY" \
    --data-urlencode "handle=$h" \
    -o "$out"
done

##############################################################################
# TRUTH SOCIAL — posts (needs explicit post URLs)
##############################################################################
truth_posts=(
  "https://truthsocial.com/@realDonaldTrump/posts/113143847892847392"
  # add more post URLs as discovered
)
for url in "${truth_posts[@]}"; do
  out="data/truth_social/$(sanitize "$url").json"
  curl -sS --fail-with-body -G 'https://api.scrapecreators.com/v1/truthsocial/post' \
    -H "x-api-key: $SC_API_KEY" \
    --data-urlencode "url=$url" \
    -o "$out"
done

echo "Done."


