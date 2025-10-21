"""
时间处理工具模块
"""
from datetime import datetime, timedelta
from typing import Optional, Tuple
import loguru

logger = loguru.logger


def parse_time_range(time_range_str: str, current_time: Optional[datetime] = None) -> Tuple[Optional[str], Optional[str]]:
    """
    解析时间范围字符串，返回开始和结束时间
    
    Args:
        time_range_str: 时间范围字符串，如 "today", "yesterday", "last_3_days"
        current_time: 当前时间，默认为系统当前时间
        
    Returns:
        (开始时间, 结束时间) 的元组，格式为 "YYYY-MM-DD HH:MM:SS"
    """
    if not time_range_str:
        return None, None
    
    if current_time is None:
        current_time = datetime.now()
    
    # 获取今天的开始和结束
    today_start = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = current_time.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    try:
        time_range_lower = time_range_str.lower().strip()
        
        # 相对日期
        if time_range_lower == "today":
            return _format_range(today_start, today_end)
        
        if time_range_lower == "yesterday":
            return _format_range(today_start - timedelta(days=1), today_end - timedelta(days=1))
        
        if time_range_lower == "day_before_yesterday":
            return _format_range(today_start - timedelta(days=2), today_end - timedelta(days=2))
        
        if time_range_lower in ["recent", "recent_days"]:
            return _format_range(today_start - timedelta(days=2), today_end)
        
        # 周范围
        if time_range_lower == "this_week":
            weekday = current_time.weekday()
            return _format_range(today_start - timedelta(days=weekday), today_end)
        
        if time_range_lower == "last_week":
            weekday = current_time.weekday()
            last_week_end = (today_start - timedelta(days=weekday + 1)).replace(hour=23, minute=59, second=59)
            last_week_start = last_week_end.replace(hour=0, minute=0, second=0) - timedelta(days=6)
            return _format_range(last_week_start, last_week_end)
        
        # 月范围
        if time_range_lower == "this_month":
            month_start = current_time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            return _format_range(month_start, today_end)
        
        if time_range_lower == "last_month":
            first_day_this_month = current_time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            last_month_end = (first_day_this_month - timedelta(days=1)).replace(hour=23, minute=59, second=59)
            last_month_start = last_month_end.replace(day=1, hour=0, minute=0, second=0)
            return _format_range(last_month_start, last_month_end)
        
        # 过去N天
        if time_range_lower.startswith("last_") and time_range_lower.endswith("_days"):
            try:
                days = int(time_range_lower.split("_")[1])
                return _format_range(today_start - timedelta(days=days-1), today_end)
            except (ValueError, IndexError):
                logger.warning(f"无法解析天数: {time_range_str}")
                return None, None
        
        # 过去N小时
        if time_range_lower.startswith("last_") and time_range_lower.endswith("_hours"):
            try:
                hours = int(time_range_lower.split("_")[1])
                return _format_range(current_time - timedelta(hours=hours), current_time)
            except (ValueError, IndexError):
                logger.warning(f"无法解析小时数: {time_range_str}")
                return None, None
        
        # 具体日期范围 (YYYY-MM-DD,YYYY-MM-DD)
        if "," in time_range_str:
            dates = time_range_str.split(",")
            if len(dates) == 2:
                start_date = datetime.strptime(dates[0].strip(), "%Y-%m-%d")
                end_date = datetime.strptime(dates[1].strip(), "%Y-%m-%d")
                return _format_range(
                    start_date.replace(hour=0, minute=0, second=0),
                    end_date.replace(hour=23, minute=59, second=59)
                )
        
        # 具体日期 (YYYY-MM-DD)
        if len(time_range_str) == 10 and time_range_str.count("-") == 2:
            specific_date = datetime.strptime(time_range_str, "%Y-%m-%d")
            return _format_range(
                specific_date.replace(hour=0, minute=0, second=0),
                specific_date.replace(hour=23, minute=59, second=59)
            )
        
        # 时间段
        if time_range_lower in ["morning", "afternoon", "evening"]:
            if time_range_lower == "morning":
                return _format_range(
                    today_start.replace(hour=6, minute=0),
                    today_start.replace(hour=11, minute=59, second=59)
                )
            elif time_range_lower == "afternoon":
                return _format_range(
                    today_start.replace(hour=12, minute=0),
                    today_start.replace(hour=17, minute=59, second=59)
                )
            else:  # evening
                return _format_range(
                    today_start.replace(hour=18, minute=0),
                    today_start.replace(hour=23, minute=59, second=59)
                )
        
        logger.warning(f"未识别的时间范围格式: {time_range_str}")
        return None, None
        
    except Exception as e:
        logger.error(f"解析时间范围失败: {time_range_str}, 错误: {e}")
        return None, None


def _format_range(start: datetime, end: datetime) -> Tuple[str, str]:
    """格式化时间范围"""
    return start.strftime("%Y-%m-%d %H:%M:%S"), end.strftime("%Y-%m-%d %H:%M:%S")

