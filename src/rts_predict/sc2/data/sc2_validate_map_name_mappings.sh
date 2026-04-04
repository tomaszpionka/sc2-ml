#!/usr/bin/env bash

set -euo pipefail

BASE_DIR="$HOME/Downloads/SC2_Replays"
TARGET_NAME="map_foreign_to_english_mapping.json"

tmp_file="$(mktemp)"
found_any=0

echo "Checking mapping files..."

for dir in "$BASE_DIR"/20*; do
    [[ -d "$dir" ]] || continue

    file="$dir/$TARGET_NAME"

    if [[ ! -f "$file" ]]; then
        echo "MISSING  $dir"
        continue
    fi

    found_any=1

    if command -v jq >/dev/null 2>&1; then
        hash="$(jq -S . "$file" | shasum | awk '{print $1}')"
    else
        hash="$(shasum "$file" | awk '{print $1}')"
    fi

    printf '%s\t%s\n' "$hash" "$dir" >> "$tmp_file"
done

echo

if [[ "$found_any" -eq 0 ]]; then
    echo "No matching subdirectories or mapping files found."
    rm -f "$tmp_file"
    exit 1
fi

unique_hash_count="$(cut -f1 "$tmp_file" | sort | uniq | wc -l | tr -d ' ')"

if [[ "$unique_hash_count" -eq 1 ]]; then
    echo "✅ All mapping files are identical"
else
    echo "❌ Differences found!"
    echo

    sort "$tmp_file" | while IFS=$'\t' read -r hash dir; do
        printf '%s  %s\n' "$hash" "$dir"
    done

    echo
    echo "Grouped summary:"
    cut -f1 "$tmp_file" | sort | uniq | while read -r hash; do
        echo "Hash: $hash"
        awk -F '\t' -v h="$hash" '$1 == h { print "  " $2 }' "$tmp_file"
        echo
    done
fi

rm -f "$tmp_file"

# Checking mapping files...

# ❌ Differences found!

# 5c08e7f654e66cb24b1e84b468d0ddce8f0d6fb3  /Users/tomaszpionka/Downloads/SC2_Replays/2016_IEM_10_Taipei
# 5c08e7f654e66cb24b1e84b468d0ddce8f0d6fb3  /Users/tomaszpionka/Downloads/SC2_Replays/2016_IEM_11_Shanghai
# 5c08e7f654e66cb24b1e84b468d0ddce8f0d6fb3  /Users/tomaszpionka/Downloads/SC2_Replays/2017_IEM_XI_World_Championship_Katowice
# 5c08e7f654e66cb24b1e84b468d0ddce8f0d6fb3  /Users/tomaszpionka/Downloads/SC2_Replays/2017_WCS_Austin
# 5c08e7f654e66cb24b1e84b468d0ddce8f0d6fb3  /Users/tomaszpionka/Downloads/SC2_Replays/2017_WCS_Global_Finals
# 5c08e7f654e66cb24b1e84b468d0ddce8f0d6fb3  /Users/tomaszpionka/Downloads/SC2_Replays/2017_WCS_Jonkoping
# 5c08e7f654e66cb24b1e84b468d0ddce8f0d6fb3  /Users/tomaszpionka/Downloads/SC2_Replays/2017_WCS_Montreal
# 5c08e7f654e66cb24b1e84b468d0ddce8f0d6fb3  /Users/tomaszpionka/Downloads/SC2_Replays/2017_WESG_Barcelona
# 5c08e7f654e66cb24b1e84b468d0ddce8f0d6fb3  /Users/tomaszpionka/Downloads/SC2_Replays/2017_WESG_Haikou
# 5c08e7f654e66cb24b1e84b468d0ddce8f0d6fb3  /Users/tomaszpionka/Downloads/SC2_Replays/2018_Cheeseadelphia_8
# 5c08e7f654e66cb24b1e84b468d0ddce8f0d6fb3  /Users/tomaszpionka/Downloads/SC2_Replays/2018_IEM_Katowice
# 5c08e7f654e66cb24b1e84b468d0ddce8f0d6fb3  /Users/tomaszpionka/Downloads/SC2_Replays/2018_IEM_PyeongChang
# 5c08e7f654e66cb24b1e84b468d0ddce8f0d6fb3  /Users/tomaszpionka/Downloads/SC2_Replays/2018_WCS_Austin
# 5c08e7f654e66cb24b1e84b468d0ddce8f0d6fb3  /Users/tomaszpionka/Downloads/SC2_Replays/2018_WCS_Leipzig
# 5c08e7f654e66cb24b1e84b468d0ddce8f0d6fb3  /Users/tomaszpionka/Downloads/SC2_Replays/2018_WCS_Montreal
# 5c08e7f654e66cb24b1e84b468d0ddce8f0d6fb3  /Users/tomaszpionka/Downloads/SC2_Replays/2018_WESG_Grand_Finals
# 5c08e7f654e66cb24b1e84b468d0ddce8f0d6fb3  /Users/tomaszpionka/Downloads/SC2_Replays/2019_Assembly_Summer
# 5c08e7f654e66cb24b1e84b468d0ddce8f0d6fb3  /Users/tomaszpionka/Downloads/SC2_Replays/2019_HomeStory_Cup_XIX
# 5c08e7f654e66cb24b1e84b468d0ddce8f0d6fb3  /Users/tomaszpionka/Downloads/SC2_Replays/2019_HomeStory_Cup_XX
# 5c08e7f654e66cb24b1e84b468d0ddce8f0d6fb3  /Users/tomaszpionka/Downloads/SC2_Replays/2019_IEM_Katowice
# 5c08e7f654e66cb24b1e84b468d0ddce8f0d6fb3  /Users/tomaszpionka/Downloads/SC2_Replays/2019_WCS_Grand_Finals
# 5c08e7f654e66cb24b1e84b468d0ddce8f0d6fb3  /Users/tomaszpionka/Downloads/SC2_Replays/2019_WCS_Winter
# 5c08e7f654e66cb24b1e84b468d0ddce8f0d6fb3  /Users/tomaszpionka/Downloads/SC2_Replays/2020_05_Dreamhack_Last_Chance
# 5c08e7f654e66cb24b1e84b468d0ddce8f0d6fb3  /Users/tomaszpionka/Downloads/SC2_Replays/2020_StayAtHome_Story_Cup_1
# 5c08e7f654e66cb24b1e84b468d0ddce8f0d6fb3  /Users/tomaszpionka/Downloads/SC2_Replays/2020_TSL5
# 5c08e7f654e66cb24b1e84b468d0ddce8f0d6fb3  /Users/tomaszpionka/Downloads/SC2_Replays/2020_TSL6
# 5c08e7f654e66cb24b1e84b468d0ddce8f0d6fb3  /Users/tomaszpionka/Downloads/SC2_Replays/2021_Dreamhack_SC2_Masters_Summer
# 5c08e7f654e66cb24b1e84b468d0ddce8f0d6fb3  /Users/tomaszpionka/Downloads/SC2_Replays/2021_Dreamhack_SC2_Masters_Winter
# 5c08e7f654e66cb24b1e84b468d0ddce8f0d6fb3  /Users/tomaszpionka/Downloads/SC2_Replays/2021_StayAtHome_Story_Cup_3
# 5c08e7f654e66cb24b1e84b468d0ddce8f0d6fb3  /Users/tomaszpionka/Downloads/SC2_Replays/2021_StayAtHome_Story_Cup_4
# 5c08e7f654e66cb24b1e84b468d0ddce8f0d6fb3  /Users/tomaszpionka/Downloads/SC2_Replays/2021_TSL7
# 5c08e7f654e66cb24b1e84b468d0ddce8f0d6fb3  /Users/tomaszpionka/Downloads/SC2_Replays/2022_Dreamhack_SC2_Masters_Last_Chance2021
# 5c08e7f654e66cb24b1e84b468d0ddce8f0d6fb3  /Users/tomaszpionka/Downloads/SC2_Replays/2022_Dreamhack_SC2_Masters_Valencia
# 5c08e7f654e66cb24b1e84b468d0ddce8f0d6fb3  /Users/tomaszpionka/Downloads/SC2_Replays/2022_HomeStory_Cup_XXI
# 5c08e7f654e66cb24b1e84b468d0ddce8f0d6fb3  /Users/tomaszpionka/Downloads/SC2_Replays/2022_TSL9
# 5c08e7f654e66cb24b1e84b468d0ddce8f0d6fb3  /Users/tomaszpionka/Downloads/SC2_Replays/2023_01_IEM_Katowice
# 5c08e7f654e66cb24b1e84b468d0ddce8f0d6fb3  /Users/tomaszpionka/Downloads/SC2_Replays/2023_05_Gamers8
# 5c08e7f654e66cb24b1e84b468d0ddce8f0d6fb3  /Users/tomaszpionka/Downloads/SC2_Replays/2023_HomeStory_Cup_XXIV
# 5c08e7f654e66cb24b1e84b468d0ddce8f0d6fb3  /Users/tomaszpionka/Downloads/SC2_Replays/2024_03_ESL_SC2_Masters_Spring_Finals
# 5c08e7f654e66cb24b1e84b468d0ddce8f0d6fb3  /Users/tomaszpionka/Downloads/SC2_Replays/2024_HomeStory_Cup_XXV
# 5c08e7f654e66cb24b1e84b468d0ddce8f0d6fb3  /Users/tomaszpionka/Downloads/SC2_Replays/2024_HomeStory_Cup_XXVI
# 5c08e7f654e66cb24b1e84b468d0ddce8f0d6fb3  /Users/tomaszpionka/Downloads/SC2_Replays/2024_StaraZagora_BellumGensElite
# 7acb293d4f4ab2c8d2a7b9e57f6ac4c20edcbebe  /Users/tomaszpionka/Downloads/SC2_Replays/2016_WCS_Winter
# 7acb293d4f4ab2c8d2a7b9e57f6ac4c20edcbebe  /Users/tomaszpionka/Downloads/SC2_Replays/2017_HomeStory_Cup_XV
# 7acb293d4f4ab2c8d2a7b9e57f6ac4c20edcbebe  /Users/tomaszpionka/Downloads/SC2_Replays/2017_HomeStory_Cup_XVI
# 7acb293d4f4ab2c8d2a7b9e57f6ac4c20edcbebe  /Users/tomaszpionka/Downloads/SC2_Replays/2017_IEM_Shanghai
# 7acb293d4f4ab2c8d2a7b9e57f6ac4c20edcbebe  /Users/tomaszpionka/Downloads/SC2_Replays/2018_HomeStory_Cup_XVII
# 7acb293d4f4ab2c8d2a7b9e57f6ac4c20edcbebe  /Users/tomaszpionka/Downloads/SC2_Replays/2018_HomeStory_Cup_XVIII
# 7acb293d4f4ab2c8d2a7b9e57f6ac4c20edcbebe  /Users/tomaszpionka/Downloads/SC2_Replays/2018_WCS_Global_Finals
# 7acb293d4f4ab2c8d2a7b9e57f6ac4c20edcbebe  /Users/tomaszpionka/Downloads/SC2_Replays/2018_WCS_Valencia
# 7acb293d4f4ab2c8d2a7b9e57f6ac4c20edcbebe  /Users/tomaszpionka/Downloads/SC2_Replays/2019_WCS_Fall
# 7acb293d4f4ab2c8d2a7b9e57f6ac4c20edcbebe  /Users/tomaszpionka/Downloads/SC2_Replays/2019_WCS_Spring
# 7acb293d4f4ab2c8d2a7b9e57f6ac4c20edcbebe  /Users/tomaszpionka/Downloads/SC2_Replays/2019_WCS_Summer
# 7acb293d4f4ab2c8d2a7b9e57f6ac4c20edcbebe  /Users/tomaszpionka/Downloads/SC2_Replays/2020_ASUS_ROG_Online
# 7acb293d4f4ab2c8d2a7b9e57f6ac4c20edcbebe  /Users/tomaszpionka/Downloads/SC2_Replays/2020_Dreamhack_SC2_Masters_Fall
# 7acb293d4f4ab2c8d2a7b9e57f6ac4c20edcbebe  /Users/tomaszpionka/Downloads/SC2_Replays/2020_Dreamhack_SC2_Masters_Summer
# 7acb293d4f4ab2c8d2a7b9e57f6ac4c20edcbebe  /Users/tomaszpionka/Downloads/SC2_Replays/2020_IEM_Katowice
# 7acb293d4f4ab2c8d2a7b9e57f6ac4c20edcbebe  /Users/tomaszpionka/Downloads/SC2_Replays/2020_StayAtHome_Story_Cup_2
# 7acb293d4f4ab2c8d2a7b9e57f6ac4c20edcbebe  /Users/tomaszpionka/Downloads/SC2_Replays/2021_ASUS_ROG_Fall
# 7acb293d4f4ab2c8d2a7b9e57f6ac4c20edcbebe  /Users/tomaszpionka/Downloads/SC2_Replays/2021_Cheeseadelphia_Winter_Championship
# 7acb293d4f4ab2c8d2a7b9e57f6ac4c20edcbebe  /Users/tomaszpionka/Downloads/SC2_Replays/2021_Dreamhack_SC2_Masters_Fall
# 7acb293d4f4ab2c8d2a7b9e57f6ac4c20edcbebe  /Users/tomaszpionka/Downloads/SC2_Replays/2021_IEM_Katowice
# 7acb293d4f4ab2c8d2a7b9e57f6ac4c20edcbebe  /Users/tomaszpionka/Downloads/SC2_Replays/2021_TSL8
# 7acb293d4f4ab2c8d2a7b9e57f6ac4c20edcbebe  /Users/tomaszpionka/Downloads/SC2_Replays/2022_03_DH_SC2_Masters_Atlanta
# 7acb293d4f4ab2c8d2a7b9e57f6ac4c20edcbebe  /Users/tomaszpionka/Downloads/SC2_Replays/2022_HomeStory_Cup_XXII
# 7acb293d4f4ab2c8d2a7b9e57f6ac4c20edcbebe  /Users/tomaszpionka/Downloads/SC2_Replays/2022_IEM_Katowice
# 7acb293d4f4ab2c8d2a7b9e57f6ac4c20edcbebe  /Users/tomaszpionka/Downloads/SC2_Replays/2023_04_ESL_SC2_Masters_Summer_Finals
# 7acb293d4f4ab2c8d2a7b9e57f6ac4c20edcbebe  /Users/tomaszpionka/Downloads/SC2_Replays/2023_07_ESL_SC2_Masters_Winter_Finals
# 7acb293d4f4ab2c8d2a7b9e57f6ac4c20edcbebe  /Users/tomaszpionka/Downloads/SC2_Replays/2024_01_IEM_Katowice
# 7acb293d4f4ab2c8d2a7b9e57f6ac4c20edcbebe  /Users/tomaszpionka/Downloads/SC2_Replays/2024_05_EWC

# Grouped summary:
# Hash: 5c08e7f654e66cb24b1e84b468d0ddce8f0d6fb3
#   /Users/tomaszpionka/Downloads/SC2_Replays/2016_IEM_10_Taipei
#   /Users/tomaszpionka/Downloads/SC2_Replays/2016_IEM_11_Shanghai
#   /Users/tomaszpionka/Downloads/SC2_Replays/2017_IEM_XI_World_Championship_Katowice
#   /Users/tomaszpionka/Downloads/SC2_Replays/2017_WCS_Austin
#   /Users/tomaszpionka/Downloads/SC2_Replays/2017_WCS_Global_Finals
#   /Users/tomaszpionka/Downloads/SC2_Replays/2017_WCS_Jonkoping
#   /Users/tomaszpionka/Downloads/SC2_Replays/2017_WCS_Montreal
#   /Users/tomaszpionka/Downloads/SC2_Replays/2017_WESG_Barcelona
#   /Users/tomaszpionka/Downloads/SC2_Replays/2017_WESG_Haikou
#   /Users/tomaszpionka/Downloads/SC2_Replays/2018_Cheeseadelphia_8
#   /Users/tomaszpionka/Downloads/SC2_Replays/2018_IEM_Katowice
#   /Users/tomaszpionka/Downloads/SC2_Replays/2018_IEM_PyeongChang
#   /Users/tomaszpionka/Downloads/SC2_Replays/2018_WCS_Austin
#   /Users/tomaszpionka/Downloads/SC2_Replays/2018_WCS_Leipzig
#   /Users/tomaszpionka/Downloads/SC2_Replays/2018_WCS_Montreal
#   /Users/tomaszpionka/Downloads/SC2_Replays/2018_WESG_Grand_Finals
#   /Users/tomaszpionka/Downloads/SC2_Replays/2019_Assembly_Summer
#   /Users/tomaszpionka/Downloads/SC2_Replays/2019_HomeStory_Cup_XIX
#   /Users/tomaszpionka/Downloads/SC2_Replays/2019_HomeStory_Cup_XX
#   /Users/tomaszpionka/Downloads/SC2_Replays/2019_IEM_Katowice
#   /Users/tomaszpionka/Downloads/SC2_Replays/2019_WCS_Grand_Finals
#   /Users/tomaszpionka/Downloads/SC2_Replays/2019_WCS_Winter
#   /Users/tomaszpionka/Downloads/SC2_Replays/2020_05_Dreamhack_Last_Chance
#   /Users/tomaszpionka/Downloads/SC2_Replays/2020_StayAtHome_Story_Cup_1
#   /Users/tomaszpionka/Downloads/SC2_Replays/2020_TSL5
#   /Users/tomaszpionka/Downloads/SC2_Replays/2020_TSL6
#   /Users/tomaszpionka/Downloads/SC2_Replays/2021_Dreamhack_SC2_Masters_Summer
#   /Users/tomaszpionka/Downloads/SC2_Replays/2021_Dreamhack_SC2_Masters_Winter
#   /Users/tomaszpionka/Downloads/SC2_Replays/2021_StayAtHome_Story_Cup_3
#   /Users/tomaszpionka/Downloads/SC2_Replays/2021_StayAtHome_Story_Cup_4
#   /Users/tomaszpionka/Downloads/SC2_Replays/2021_TSL7
#   /Users/tomaszpionka/Downloads/SC2_Replays/2022_Dreamhack_SC2_Masters_Last_Chance2021
#   /Users/tomaszpionka/Downloads/SC2_Replays/2022_Dreamhack_SC2_Masters_Valencia
#   /Users/tomaszpionka/Downloads/SC2_Replays/2022_HomeStory_Cup_XXI
#   /Users/tomaszpionka/Downloads/SC2_Replays/2022_TSL9
#   /Users/tomaszpionka/Downloads/SC2_Replays/2023_01_IEM_Katowice
#   /Users/tomaszpionka/Downloads/SC2_Replays/2023_05_Gamers8
#   /Users/tomaszpionka/Downloads/SC2_Replays/2023_HomeStory_Cup_XXIV
#   /Users/tomaszpionka/Downloads/SC2_Replays/2024_03_ESL_SC2_Masters_Spring_Finals
#   /Users/tomaszpionka/Downloads/SC2_Replays/2024_HomeStory_Cup_XXV
#   /Users/tomaszpionka/Downloads/SC2_Replays/2024_HomeStory_Cup_XXVI
#   /Users/tomaszpionka/Downloads/SC2_Replays/2024_StaraZagora_BellumGensElite

# Hash: 7acb293d4f4ab2c8d2a7b9e57f6ac4c20edcbebe
#   /Users/tomaszpionka/Downloads/SC2_Replays/2016_WCS_Winter
#   /Users/tomaszpionka/Downloads/SC2_Replays/2017_HomeStory_Cup_XV
#   /Users/tomaszpionka/Downloads/SC2_Replays/2017_HomeStory_Cup_XVI
#   /Users/tomaszpionka/Downloads/SC2_Replays/2017_IEM_Shanghai
#   /Users/tomaszpionka/Downloads/SC2_Replays/2018_HomeStory_Cup_XVII
#   /Users/tomaszpionka/Downloads/SC2_Replays/2018_HomeStory_Cup_XVIII
#   /Users/tomaszpionka/Downloads/SC2_Replays/2018_WCS_Global_Finals
#   /Users/tomaszpionka/Downloads/SC2_Replays/2018_WCS_Valencia
#   /Users/tomaszpionka/Downloads/SC2_Replays/2019_WCS_Fall
#   /Users/tomaszpionka/Downloads/SC2_Replays/2019_WCS_Spring
#   /Users/tomaszpionka/Downloads/SC2_Replays/2019_WCS_Summer
#   /Users/tomaszpionka/Downloads/SC2_Replays/2020_ASUS_ROG_Online
#   /Users/tomaszpionka/Downloads/SC2_Replays/2020_Dreamhack_SC2_Masters_Fall
#   /Users/tomaszpionka/Downloads/SC2_Replays/2020_Dreamhack_SC2_Masters_Summer
#   /Users/tomaszpionka/Downloads/SC2_Replays/2020_IEM_Katowice
#   /Users/tomaszpionka/Downloads/SC2_Replays/2020_StayAtHome_Story_Cup_2
#   /Users/tomaszpionka/Downloads/SC2_Replays/2021_ASUS_ROG_Fall
#   /Users/tomaszpionka/Downloads/SC2_Replays/2021_Cheeseadelphia_Winter_Championship
#   /Users/tomaszpionka/Downloads/SC2_Replays/2021_Dreamhack_SC2_Masters_Fall
#   /Users/tomaszpionka/Downloads/SC2_Replays/2021_IEM_Katowice
#   /Users/tomaszpionka/Downloads/SC2_Replays/2021_TSL8
#   /Users/tomaszpionka/Downloads/SC2_Replays/2022_03_DH_SC2_Masters_Atlanta
#   /Users/tomaszpionka/Downloads/SC2_Replays/2022_HomeStory_Cup_XXII
#   /Users/tomaszpionka/Downloads/SC2_Replays/2022_IEM_Katowice
#   /Users/tomaszpionka/Downloads/SC2_Replays/2023_04_ESL_SC2_Masters_Summer_Finals
#   /Users/tomaszpionka/Downloads/SC2_Replays/2023_07_ESL_SC2_Masters_Winter_Finals
#   /Users/tomaszpionka/Downloads/SC2_Replays/2024_01_IEM_Katowice
#   /Users/tomaszpionka/Downloads/SC2_Replays/2024_05_EWC