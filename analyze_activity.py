"""
プレイヤーのログイン（プレイ）状況を分析するスクリプト

resultファイルのrankScoreとcashoutsの変化を追跡して、
いつプレイしていたかを特定します。
"""

import json
import os
import glob
from datetime import datetime
from typing import Optional

# =============================================================================
# 設定
# =============================================================================

# 結果ファイルのフォルダ
RESULTS_FOLDER = os.path.dirname(os.path.abspath(__file__))

# 結果ファイルのパターン
RESULT_PATTERN = "result_*.json"


# =============================================================================
# 分析関数
# =============================================================================

def load_result_file(filepath: str) -> Optional[dict]:
    """結果ファイルを読み込む"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[警告] ファイル読み込みエラー: {filepath} - {e}")
        return None


def extract_player_data(result: dict) -> dict:
    """結果ファイルからプレイヤーデータを抽出"""
    data = {
        "timestamp": result.get("timestamp", ""),
        "rankScore": None,
        "rank": None,
        "cashouts": None,
        "worldTourRank": None,
        "playerName": None,
    }
    
    # ランクリーダーボードからデータ抽出
    ranked = result.get("ranked_leaderboard", {})
    if ranked and ranked.get("data"):
        player = ranked["data"][0]
        data["rankScore"] = player.get("rankScore")
        data["rank"] = player.get("rank")
        data["playerName"] = player.get("name")
    
    # ワールドツアーからデータ抽出
    world_tour = result.get("world_tour", {})
    if world_tour and world_tour.get("data"):
        player = world_tour["data"][0]
        data["cashouts"] = player.get("cashouts")
        data["worldTourRank"] = player.get("rank")
    
    return data


def format_timestamp(iso_timestamp: str) -> str:
    """タイムスタンプを読みやすい形式に変換"""
    try:
        dt = datetime.fromisoformat(iso_timestamp)
        return dt.strftime("%Y/%m/%d %H:%M:%S")
    except:
        return iso_timestamp


def format_number(num: Optional[int]) -> str:
    """数値をフォーマット"""
    if num is None:
        return "N/A"
    return f"{num:,}"


def analyze_activity():
    """アクティビティを分析"""
    # 結果ファイルを収集
    pattern = os.path.join(RESULTS_FOLDER, RESULT_PATTERN)
    files = sorted(glob.glob(pattern))
    
    if len(files) == 0:
        print("結果ファイルが見つかりません。")
        return
    
    print("=" * 80)
    print("[GAME] THE FINALS - Player Activity Analysis")
    print("=" * 80)
    print(f"Files to analyze: {len(files)}\n")
    
    # データを読み込み
    all_data = []
    for filepath in files:
        result = load_result_file(filepath)
        if result:
            player_data = extract_player_data(result)
            player_data["filename"] = os.path.basename(filepath)
            all_data.append(player_data)
    
    if len(all_data) == 0:
        print("有効なデータがありません。")
        return
    
    # タイムスタンプでソート
    all_data.sort(key=lambda x: x["timestamp"])
    
    # プレイヤー名を表示
    player_name = all_data[0].get("playerName", "Unknown")
    print(f"Player: {player_name}")
    print("-" * 80)
    
    # 変化を分析
    print("\n[DATA] History and Changes:\n")
    print(f"{'Timestamp':<22} | {'Rank':>8} | {'RankScore':>12} | {'Cashouts':>18} | {'Status':<15}")
    print("-" * 90)
    
    activity_periods = []
    prev_data = None
    
    for data in all_data:
        timestamp = format_timestamp(data["timestamp"])
        rank = data.get("rank")
        rank_score = data.get("rankScore")
        cashouts = data.get("cashouts")
        
        # 変化を検出
        status = ""
        rank_change = ""
        score_change = ""
        cashout_change = ""
        
        if prev_data:
            prev_score = prev_data.get("rankScore")
            prev_cashouts = prev_data.get("cashouts")
            
            score_diff = 0
            cashout_diff = 0
            
            if rank_score is not None and prev_score is not None:
                score_diff = rank_score - prev_score
                if score_diff != 0:
                    sign = "+" if score_diff > 0 else ""
                    score_change = f"({sign}{score_diff})"
            
            if cashouts is not None and prev_cashouts is not None:
                cashout_diff = cashouts - prev_cashouts
                if cashout_diff != 0:
                    sign = "+" if cashout_diff > 0 else ""
                    cashout_change = f"({sign}{cashout_diff:,})"
            
            # アクティビティ判定
            if score_diff != 0 or cashout_diff != 0:
                status = "[ACTIVE] Playing"
                activity_periods.append({
                    "start": prev_data["timestamp"],
                    "end": data["timestamp"],
                    "score_change": score_diff,
                    "cashout_change": cashout_diff,
                })
            else:
                status = "[--] No change"
        else:
            status = "[START] First"
        
        # 表示
        rank_str = f"#{rank}" if rank else "N/A"
        score_str = f"{format_number(rank_score)}"
        if score_change:
            score_str += f" {score_change}"
        
        cashout_str = format_number(cashouts)
        if cashout_change:
            cashout_str += f" {cashout_change}"
        
        print(f"{timestamp:<22} | {rank_str:>8} | {score_str:>12} | {cashout_str:>18} | {status:<15}")
        
        prev_data = data
    
    # サマリー
    print("\n" + "=" * 80)
    print("[SUMMARY] Activity Summary")
    print("=" * 80)
    
    if len(activity_periods) > 0:
        print(f"\nDetected play sessions: {len(activity_periods)}\n")
        
        total_score_change = 0
        total_cashout_change = 0
        
        for i, period in enumerate(activity_periods, 1):
            start = format_timestamp(period["start"])
            end = format_timestamp(period["end"])
            score = period["score_change"]
            cashout = period["cashout_change"]
            
            total_score_change += score
            total_cashout_change += cashout
            
            score_sign = "+" if score >= 0 else ""
            cashout_sign = "+" if cashout >= 0 else ""
            
            print(f"  [{i}] {start} - {end}")
            print(f"      RankScore: {score_sign}{score} | Cashouts: {cashout_sign}{cashout:,}")
            print()
        
        print("-" * 80)
        score_sign = "+" if total_score_change >= 0 else ""
        cashout_sign = "+" if total_cashout_change >= 0 else ""
        print(f"Total: RankScore {score_sign}{total_score_change} | Cashouts {cashout_sign}{total_cashout_change:,}")
    else:
        print("\nNo play activity detected.")
    
    # 最新の状態
    latest = all_data[-1]
    first = all_data[0]
    
    print("\n" + "-" * 80)
    print("[TOTAL] Overall Changes:")
    print(f"  Period: {format_timestamp(first['timestamp'])} - {format_timestamp(latest['timestamp'])}")
    
    if latest.get("rankScore") and first.get("rankScore"):
        total_score = latest["rankScore"] - first["rankScore"]
        sign = "+" if total_score >= 0 else ""
        print(f"  RankScore: {first['rankScore']:,} -> {latest['rankScore']:,} ({sign}{total_score})")
    
    if latest.get("cashouts") and first.get("cashouts"):
        total_cash = latest["cashouts"] - first["cashouts"]
        sign = "+" if total_cash >= 0 else ""
        print(f"  Cashouts: ${first['cashouts']:,} -> ${latest['cashouts']:,} ({sign}${total_cash:,})")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    analyze_activity()
