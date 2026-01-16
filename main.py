"""
THE FINALS API を使用してプレイヤー情報を取得するスクリプト

機能:
1. 特定のキーワードを名前に含むプレイヤーのランクを取得
2. ワールドトーナメント（World Tour）のキャッシュアウト情報を取得
"""

import requests
import json
import os
from datetime import datetime
from typing import Optional

# =============================================================================
# 設定
# =============================================================================

# 検索するキーワード（この名前を含むプレイヤーを検索）
SEARCH_KEYWORD = "sangwoo"  # ← ここを変更してください

# APIのベースURL
BASE_URL = "https://api.the-finals-leaderboard.com"

# 現在のシーズン（最新に合わせて変更）
CURRENT_SEASON = "s9"

# プラットフォーム
PLATFORM = "crossplay"

# 出力フォルダ（このスクリプトと同じフォルダに保存）
OUTPUT_FOLDER = os.path.dirname(os.path.abspath(__file__))


# =============================================================================
# API関数
# =============================================================================

def search_player_in_leaderboard(keyword: str, season: str = CURRENT_SEASON) -> Optional[dict]:
    """
    通常リーダーボードで特定のキーワードを含むプレイヤーを検索
    
    Args:
        keyword: 検索するプレイヤー名のキーワード
        season: シーズン（例: "s9"）
    
    Returns:
        APIレスポンス（dict）またはNone
    """
    url = f"{BASE_URL}/v1/leaderboard/{season}/{PLATFORM}"
    params = {"name": keyword}
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"[エラー] リーダーボードAPI呼び出し失敗: {e}")
        return None


def search_player_in_world_tour(keyword: str, season: str = CURRENT_SEASON) -> Optional[dict]:
    """
    ワールドツアーリーダーボードで特定のキーワードを含むプレイヤーを検索
    
    Args:
        keyword: 検索するプレイヤー名のキーワード
        season: シーズン（例: "s9"）
    
    Returns:
        APIレスポンス（dict）またはNone
    """
    url = f"{BASE_URL}/v1/leaderboard/{season}worldtour/{PLATFORM}"
    params = {"name": keyword}
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"[エラー] ワールドツアーAPI呼び出し失敗: {e}")
        return None


def save_results_to_file(ranked_data: Optional[dict], world_tour_data: Optional[dict], keyword: str):
    """
    結果をファイルに保存
    
    Args:
        ranked_data: ランクリーダーボードのデータ
        world_tour_data: ワールドツアーのデータ
        keyword: 検索キーワード
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # JSONファイルとして保存
    json_filename = os.path.join(OUTPUT_FOLDER, f"result_{timestamp}.json")
    result_data = {
        "keyword": keyword,
        "timestamp": datetime.now().isoformat(),
        "season": CURRENT_SEASON,
        "ranked_leaderboard": ranked_data,
        "world_tour": world_tour_data
    }
    
    with open(json_filename, "w", encoding="utf-8") as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n📁 JSONファイル保存: {json_filename}")


def format_cashout(cashout: int) -> str:
    """キャッシュアウト金額をフォーマット"""
    if cashout >= 1_000_000:
        return f"${cashout:,} ({cashout / 1_000_000:.2f}M)"
    elif cashout >= 1_000:
        return f"${cashout:,} ({cashout / 1_000:.1f}K)"
    else:
        return f"${cashout:,}"


def display_ranked_results(data: dict, keyword: str):
    """通常リーダーボードの結果を表示"""
    print("\n" + "=" * 60)
    print(f"🏆 ランクリーダーボード結果 (キーワード: '{keyword}')")
    print("=" * 60)
    
    if data["count"] == 0:
        print(f"'{keyword}' を含むプレイヤーは見つかりませんでした。")
        return
    
    print(f"見つかったプレイヤー数: {data['count']}")
    print("-" * 60)
    
    for player in data["data"]:
        rank = player.get("rank", "N/A")
        name = player.get("name", "Unknown")
        league = player.get("league", "N/A")
        rank_score = player.get("rankScore", "N/A")
        change = player.get("change", 0)
        club_tag = player.get("clubTag", "")
        
        # ランク変動の表示
        if change > 0:
            change_str = f"↑{change}"
        elif change < 0:
            change_str = f"↓{abs(change)}"
        else:
            change_str = "→0"
        
        club_display = f"[{club_tag}] " if club_tag else ""
        
        print(f"  #{rank} ({change_str}) | {club_display}{name}")
        print(f"       リーグ: {league} | ランクスコア: {rank_score}")
        print()


def display_world_tour_results(data: dict, keyword: str):
    """ワールドツアーリーダーボードの結果を表示"""
    print("\n" + "=" * 60)
    print(f"🌍 ワールドツアー結果 (キーワード: '{keyword}')")
    print("=" * 60)
    
    if data["count"] == 0:
        print(f"'{keyword}' を含むプレイヤーは見つかりませんでした。")
        return
    
    print(f"見つかったプレイヤー数: {data['count']}")
    print("-" * 60)
    
    for player in data["data"]:
        rank = player.get("rank", "N/A")
        name = player.get("name", "Unknown")
        cashouts = player.get("cashouts", 0)
        club_tag = player.get("clubTag", "")
        
        club_display = f"[{club_tag}] " if club_tag else ""
        cashout_formatted = format_cashout(cashouts)
        
        print(f"  #{rank} | {club_display}{name}")
        print(f"       キャッシュアウト: {cashout_formatted}")
        print()


def main():
    """メイン関数"""
    print("=" * 60)
    print("THE FINALS プレイヤー検索ツール")
    print(f"シーズン: {CURRENT_SEASON.upper()} | プラットフォーム: {PLATFORM}")
    print("=" * 60)
    
    keyword = SEARCH_KEYWORD
    
    if not keyword:
        print("[エラー] 検索キーワードが設定されていません。")
        print("SEARCH_KEYWORD 変数にキーワードを設定してください。")
        return
    
    print(f"\n検索キーワード: '{keyword}'")
    print("データを取得中...")
    
    # 1. 通常リーダーボードから検索
    ranked_data = search_player_in_leaderboard(keyword)
    if ranked_data:
        display_ranked_results(ranked_data, keyword)
    
    # 2. ワールドツアーリーダーボードから検索
    world_tour_data = search_player_in_world_tour(keyword)
    if world_tour_data:
        display_world_tour_results(world_tour_data, keyword)
    
    # 3. 結果をファイルに保存
    save_results_to_file(ranked_data, world_tour_data, keyword)
    
    print("\n" + "=" * 60)
    print("検索完了!")
    print("=" * 60)


if __name__ == "__main__":
    main()
