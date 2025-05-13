import pandas as pd
from alpha_vantage.timeseries import TimeSeries
import pandas_ta as ta
import numpy as np
from datetime import datetime, timedelta
import time
import os
import requests
from io import StringIO

# Tạo API key của Alpha Vantage - đặt key của bạn nếu có, hoặc sử dụng key thực
ALPHA_VANTAGE_API_KEY = "J50G50EZDCSTWMFN"  # API key thực cho ứng dụng này

def get_stock_data(ticker, period="1d", interval="1m"):
    """
    Lấy dữ liệu cổ phiếu từ Alpha Vantage
    
    Parameters:
        ticker (str): Mã cổ phiếu (VD: AAPL, MSFT)
        period (str): Khoảng thời gian (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
        interval (str): Khoảng cách giữa các điểm dữ liệu (1m, 5m, 15m, 30m, 60m, daily, weekly, monthly)
    
    Returns:
        DataFrame: Dữ liệu cổ phiếu với các cột Open, High, Low, Close, Volume
    """
    try:
        # Khởi tạo TimeSeries
        ts = TimeSeries(key=ALPHA_VANTAGE_API_KEY, output_format='pandas')
        
        # Chuyển đổi period và interval sang định dạng Alpha Vantage
        output_size = 'compact'  # mặc định
        if period in ['6mo', '1y', 'ytd', 'max']:
            output_size = 'full'
        
        # Lấy dữ liệu theo interval
        if interval in ['1m', '5m', '15m', '30m', '60m']:
            # Lấy dữ liệu trong ngày (intraday)
            interval_av = interval.replace('m', 'min')
            data, meta_data = ts.get_intraday(symbol=ticker, interval=interval_av, outputsize=output_size)
        elif interval == 'daily' or period in ['1d', '5d', '1mo']:
            # Lấy dữ liệu ngày
            data, meta_data = ts.get_daily(symbol=ticker, outputsize=output_size)
        elif interval == 'weekly':
            # Lấy dữ liệu tuần
            data, meta_data = ts.get_weekly(symbol=ticker)
        elif interval == 'monthly':
            # Lấy dữ liệu tháng
            data, meta_data = ts.get_monthly(symbol=ticker)
        else:
            # Mặc định lấy dữ liệu ngày
            data, meta_data = ts.get_daily(symbol=ticker, outputsize=output_size)
        
        # Đổi tên cột để đồng nhất
        data.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        
        # Lọc dữ liệu theo period
        if period == '1d':
            data = data.head(390)  # ~6.5 giờ giao dịch (390 phút)
        elif period == '5d':
            data = data.head(5 * 390)  # 5 ngày
        elif period == '1mo':
            data = data.head(21)  # ~21 ngày giao dịch trong tháng
        elif period == '6mo':
            data = data.head(126)  # ~6 tháng (21 ngày * 6)
        elif period == '1y':
            data = data.head(252)  # ~1 năm (252 ngày giao dịch)
            
        # Sắp xếp lại theo thời gian tăng dần
        data = data.sort_index()
        
        return data
    except Exception as e:
        print(f"Lỗi khi lấy dữ liệu cho {ticker}: {e}")
        # Nếu lỗi, trả về dữ liệu mẫu
        return get_sample_data(ticker)

def get_sample_data(ticker):
    """
    Tạo dữ liệu mẫu nếu không lấy được dữ liệu thật
    
    Parameters:
        ticker (str): Mã cổ phiếu
    
    Returns:
        DataFrame: Dữ liệu mẫu với các cột Open, High, Low, Close, Volume
    """
    # Tạo dữ liệu mẫu trong 100 ngày
    today = datetime.now()
    dates = [today - timedelta(days=i) for i in range(100)]
    dates.reverse()
    
    # Tạo các giá trị mẫu
    np.random.seed(42)  # Để có kết quả nhất quán
    
    # Giá khởi điểm
    base_price = 100.0 if ticker not in ["BTC-USD", "ETH-USD"] else 10000.0
    
    # Sinh dữ liệu giả
    close_prices = [base_price]
    for i in range(1, 100):
        close_prices.append(close_prices[-1] * (1 + np.random.normal(0, 0.02)))
    
    # Tạo các cột khác
    opens = [price * (1 + np.random.normal(0, 0.005)) for price in close_prices]
    highs = [max(o, c) * (1 + abs(np.random.normal(0, 0.01))) for o, c in zip(opens, close_prices)]
    lows = [min(o, c) * (1 - abs(np.random.normal(0, 0.01))) for o, c in zip(opens, close_prices)]
    volumes = [int(np.random.normal(1000000, 200000)) for _ in range(100)]
    
    # Tạo DataFrame
    df = pd.DataFrame({
        'Open': opens,
        'High': highs,
        'Low': lows,
        'Close': close_prices,
        'Volume': volumes
    }, index=dates)
    
    return df

def calculate_indicators(df):
    """
    Tính toán các chỉ báo kỹ thuật trên DataFrame
    
    Parameters:
        df (DataFrame): DataFrame chứa dữ liệu giá cổ phiếu
    
    Returns:
        DataFrame: DataFrame ban đầu với thêm các cột chỉ báo
    """
    if df.empty:
        return df
    
    # Tính RSI
    df['RSI'] = ta.rsi(df['Close'], length=14)
    
    # Tính MACD
    macd = ta.macd(df['Close'])
    df['MACD'] = macd['MACD_12_26_9']
    df['MACD_Signal'] = macd['MACDs_12_26_9']
    df['MACD_Hist'] = macd['MACDh_12_26_9']
    
    # Tính EMA
    df['EMA_9'] = ta.ema(df['Close'], length=9)
    df['EMA_20'] = ta.ema(df['Close'], length=20)
    df['EMA_50'] = ta.ema(df['Close'], length=50)
    
    # Tính Bollinger Bands
    bbands = ta.bbands(df['Close'], length=20, std=2)
    df['BB_Upper'] = bbands['BBU_20_2.0']
    df['BB_Middle'] = bbands['BBM_20_2.0']
    df['BB_Lower'] = bbands['BBL_20_2.0']
    
    # Tính ATR (Average True Range)
    df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
    
    # Tính Stochastic Oscillator
    stoch = ta.stoch(df['High'], df['Low'], df['Close'], k=14, d=3, smooth_k=3)
    df['STOCH_K'] = stoch['STOCHk_14_3_3']
    df['STOCH_D'] = stoch['STOCHd_14_3_3']
    
    return df

def get_interval_for_timeframe(timeframe):
    """
    Xác định khoảng thời gian dữ liệu phù hợp cho từng khung thời gian
    
    Parameters:
        timeframe (str): Khung thời gian (1d, 5d, 1mo, 6mo, 1y, ytd, max)
    
    Returns:
        str: Khoảng thời gian dữ liệu phù hợp
    """
    # Chuyển đổi sang định dạng Alpha Vantage
    interval_mapping = {
        "1d": "5min",
        "5d": "15min",
        "1mo": "60min",
        "6mo": "daily",
        "1y": "daily",
        "ytd": "daily",
        "max": "weekly",
    }
    return interval_mapping.get(timeframe, "5min")

def generate_alerts(df):
    """
    Tạo danh sách cảnh báo dựa trên các chỉ báo
    
    Parameters:
        df (DataFrame): DataFrame chứa dữ liệu giá và chỉ báo
    
    Returns:
        list: Danh sách các cảnh báo
    """
    alerts = []
    
    if df.empty or len(df) < 2:
        return alerts
    
    # Lấy giá trị mới nhất và trước đó
    latest = df.iloc[-1]
    previous = df.iloc[-2]
    
    # Kiểm tra RSI
    if 'RSI' in latest and not pd.isna(latest['RSI']):
        if latest['RSI'] < 30:
            alerts.append({
                "type": "success", 
                "message": f"RSI = {latest['RSI']:.2f}: Tiềm năng tăng giá (quá bán)"
            })
        elif latest['RSI'] > 70:
            alerts.append({
                "type": "danger", 
                "message": f"RSI = {latest['RSI']:.2f}: Nguy cơ giảm giá (quá mua)"
            })
        # Kiểm tra RSI đang tăng từ vùng quá bán
        elif previous['RSI'] < 30 and latest['RSI'] > 30:
            alerts.append({
                "type": "success", 
                "message": f"RSI vừa thoát khỏi vùng quá bán: Tín hiệu tăng giá"
            })
        # Kiểm tra RSI đang giảm từ vùng quá mua
        elif previous['RSI'] > 70 and latest['RSI'] < 70:
            alerts.append({
                "type": "danger", 
                "message": f"RSI vừa thoát khỏi vùng quá mua: Tín hiệu giảm giá"
            })
    
    # Kiểm tra MACD
    if 'MACD' in latest and 'MACD_Signal' in latest:
        # MACD cắt lên đường Signal
        if latest['MACD'] > latest['MACD_Signal'] and previous['MACD'] <= previous['MACD_Signal']:
            alerts.append({
                "type": "success", 
                "message": "MACD vừa cắt lên đường Signal: Tín hiệu mua"
            })
        # MACD cắt xuống đường Signal
        elif latest['MACD'] < latest['MACD_Signal'] and previous['MACD'] >= previous['MACD_Signal']:
            alerts.append({
                "type": "danger", 
                "message": "MACD vừa cắt xuống đường Signal: Tín hiệu bán"
            })
        # MACD Histogram chuyển từ âm sang dương
        elif latest['MACD_Hist'] > 0 and previous['MACD_Hist'] <= 0:
            alerts.append({
                "type": "success", 
                "message": "MACD Histogram vừa chuyển sang dương: Động lực tăng giá"
            })
        # MACD Histogram chuyển từ dương sang âm
        elif latest['MACD_Hist'] < 0 and previous['MACD_Hist'] >= 0:
            alerts.append({
                "type": "danger", 
                "message": "MACD Histogram vừa chuyển sang âm: Động lực giảm giá"
            })
    
    # Kiểm tra EMA
    if 'EMA_9' in latest and 'EMA_20' in latest:
        # EMA 9 cắt lên EMA 20
        if latest['EMA_9'] > latest['EMA_20'] and previous['EMA_9'] <= previous['EMA_20']:
            alerts.append({
                "type": "success", 
                "message": "EMA 9 vừa cắt lên EMA 20: Xu hướng tăng ngắn hạn"
            })
        # EMA 9 cắt xuống EMA 20
        elif latest['EMA_9'] < latest['EMA_20'] and previous['EMA_9'] >= previous['EMA_20']:
            alerts.append({
                "type": "danger", 
                "message": "EMA 9 vừa cắt xuống EMA 20: Xu hướng giảm ngắn hạn"
            })
    
    # Kiểm tra giá cắt qua các đường EMA
    if 'Close' in latest and 'EMA_50' in latest:
        # Giá cắt lên EMA 50
        if latest['Close'] > latest['EMA_50'] and previous['Close'] <= previous['EMA_50']:
            alerts.append({
                "type": "success", 
                "message": "Giá vừa cắt lên EMA 50: Tín hiệu xu hướng tăng trung hạn"
            })
        # Giá cắt xuống EMA 50
        elif latest['Close'] < latest['EMA_50'] and previous['Close'] >= previous['EMA_50']:
            alerts.append({
                "type": "danger", 
                "message": "Giá vừa cắt xuống EMA 50: Tín hiệu xu hướng giảm trung hạn"
            })
    
    # Kiểm tra Bollinger Bands
    if 'BB_Upper' in latest and 'BB_Lower' in latest and 'Close' in latest:
        # Giá vượt lên trên dải Bollinger trên
        if latest['Close'] > latest['BB_Upper']:
            alerts.append({
                "type": "warning", 
                "message": "Giá vượt dải Bollinger trên: Có thể xuất hiện điều chỉnh giảm"
            })
        # Giá giảm xuống dưới dải Bollinger dưới
        elif latest['Close'] < latest['BB_Lower']:
            alerts.append({
                "type": "success", 
                "message": "Giá dưới dải Bollinger dưới: Có thể xuất hiện phục hồi"
            })
    
    return alerts

def get_popular_tickers():
    """
    Trả về danh sách các mã cổ phiếu phổ biến được nhóm theo loại
    
    Returns:
        dict: Dictionary chứa các nhóm cổ phiếu, mỗi nhóm là một dict con chứa mã cổ phiếu và tên công ty
    """
    return {
        "Cổ phiếu Mỹ - Công nghệ": {
            "AAPL": "Apple Inc.",
            "MSFT": "Microsoft Corporation",
            "GOOGL": "Alphabet Inc. (Google)",
            "AMZN": "Amazon.com Inc.",
            "META": "Meta Platforms Inc. (Facebook)",
            "TSLA": "Tesla Inc.",
            "NVDA": "NVIDIA Corporation",
            "NFLX": "Netflix Inc.",
            "INTC": "Intel Corporation",
            "AMD": "Advanced Micro Devices Inc.",
            "CSCO": "Cisco Systems Inc.",
        },
        "Cổ phiếu Mỹ - Tài chính": {
            "JPM": "JPMorgan Chase & Co.",
            "V": "Visa Inc.",
            "MA": "Mastercard Inc.",
            "BAC": "Bank of America Corporation",
            "WFC": "Wells Fargo & Company",
            "GS": "Goldman Sachs Group, Inc.",
            "C": "Citigroup Inc.",
            "AXP": "American Express Company",
        },
        "Cổ phiếu Mỹ - Tiêu dùng": {
            "WMT": "Walmart Inc.",
            "DIS": "The Walt Disney Company",
            "KO": "The Coca-Cola Company",
            "PEP": "PepsiCo Inc.",
            "MCD": "McDonald's Corporation",
            "SBUX": "Starbucks Corporation",
            "NKE": "Nike Inc.",
            "PG": "Procter & Gamble Company",
        },
        "Cổ phiếu Mỹ - Năng lượng & Viễn thông": {
            "XOM": "Exxon Mobil Corporation",
            "CVX": "Chevron Corporation",
            "T": "AT&T Inc.",
            "VZ": "Verizon Communications Inc.",
            "COP": "ConocoPhillips",
        },
        "Cổ phiếu châu Á": {
            "9988.HK": "Alibaba Group Holding (Hồng Kông)",
            "0700.HK": "Tencent Holdings (Hồng Kông)",
            "005930.KS": "Samsung Electronics (Hàn Quốc)",
            "7203.T": "Toyota Motor Corporation (Nhật Bản)",
            "9432.T": "Nippon Telegraph & Telephone (Nhật Bản)",
            "2317.TW": "Hon Hai Precision (Đài Loan, Foxconn)",
            "1299.HK": "AIA Group Limited (Hồng Kông)",
            "1398.HK": "Industrial and Commercial Bank of China (Hồng Kông)",
        },
        "ETFs": {
            "SPY": "SPDR S&P 500 ETF Trust",
            "QQQ": "Invesco QQQ Trust (NASDAQ-100)",
            "DIA": "SPDR Dow Jones Industrial Average ETF",
            "IWM": "iShares Russell 2000 ETF",
            "EEM": "iShares MSCI Emerging Markets ETF",
            "GLD": "SPDR Gold Shares",
            "SLV": "iShares Silver Trust",
            "USO": "United States Oil Fund",
            "VNQ": "Vanguard Real Estate ETF",
            "VTI": "Vanguard Total Stock Market ETF",
        },
        "Tiền điện tử": {
            "BTC-USD": "Bitcoin USD",
            "ETH-USD": "Ethereum USD",
            "XRP-USD": "XRP USD",
            "DOGE-USD": "Dogecoin USD",
            "ADA-USD": "Cardano USD",
            "SOL-USD": "Solana USD",
            "DOT-USD": "Polkadot USD",
            "AVAX-USD": "Avalanche USD",
        },
    } 