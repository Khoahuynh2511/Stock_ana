import dash
from dash import dcc, html, Input, Output, State, callback
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

# Import các hàm từ utils
from utils import (
    get_stock_data, 
    calculate_indicators, 
    generate_alerts,
    get_interval_for_timeframe,
    get_popular_tickers
)

# Khởi tạo ứng dụng Dash
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)
server = app.server
app.title = "Phân tích cổ phiếu thời gian thực"

# Danh sách các mã cổ phiếu phổ biến
popular_tickers = get_popular_tickers()

# Tạo danh sách options cho dropdown đơn giản
dropdown_options = []
popular_tickers_dict = get_popular_tickers()

for group_name, group_tickers in popular_tickers_dict.items():
    for ticker, name in group_tickers.items():
        dropdown_options.append({"label": f"{ticker} - {name}", "value": ticker})

# Hàm tạo biểu đồ
def create_chart(df, ticker, df_compare=None, compare_ticker=None):
    """Tạo biểu đồ Plotly cho dữ liệu cổ phiếu"""
    if df.empty:
        return go.Figure()
    
    # Tạo biểu đồ nến (candlestick)
    fig = go.Figure()
    
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name=ticker,
        )
    )
    
    # Thêm các đường EMA
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA_9'], name=f'{ticker} EMA 9', line=dict(color='purple', width=1)))
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA_20'], name=f'{ticker} EMA 20', line=dict(color='orange', width=1)))
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA_50'], name=f'{ticker} EMA 50', line=dict(color='green', width=1)))
    
    # Thêm Bollinger Bands
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_Upper'], name=f'{ticker} BB Upper', line=dict(color='red', width=1, dash='dash')))
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_Middle'], name=f'{ticker} BB Middle', line=dict(color='blue', width=1, dash='dash')))
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_Lower'], name=f'{ticker} BB Lower', line=dict(color='green', width=1, dash='dash')))
    
    # Thêm dữ liệu so sánh nếu có
    if df_compare is not None and not df_compare.empty and compare_ticker is not None:
        # Chuẩn hóa giá về phần trăm để dễ so sánh
        if len(df) > 0 and len(df_compare) > 0:
            # Lấy giá đóng cửa đầu tiên làm cơ sở
            df_norm = df.copy()
            df_compare_norm = df_compare.copy()
            
            base_price = df_norm['Close'].iloc[0]
            compare_base_price = df_compare_norm['Close'].iloc[0]
            
            df_norm['Close_Norm'] = (df_norm['Close'] / base_price - 1) * 100
            df_compare_norm['Close_Norm'] = (df_compare_norm['Close'] / compare_base_price - 1) * 100
            
            # Thêm đường so sánh
            fig.add_trace(go.Scatter(
                x=df_compare_norm.index,
                y=df_compare_norm['Close_Norm'],
                name=f'{compare_ticker} (% thay đổi)',
                line=dict(color='rgba(255, 0, 0, 0.7)', width=2),
                yaxis='y2'
            ))
            
            # Cấu hình trục y thứ hai
            fig.update_layout(
                yaxis2=dict(
                    title="% Thay đổi",
                    titlefont=dict(color='red'),
                    tickfont=dict(color='red'),
                    anchor="x",
                    overlaying="y",
                    side="right"
                )
            )
    
    # Cấu hình hiển thị
    chart_title = f'Biểu đồ giá {ticker}'
    if compare_ticker is not None:
        chart_title = f'So sánh {ticker} và {compare_ticker}'
        
    fig.update_layout(
        title=chart_title,
        xaxis_title='Thời gian',
        yaxis_title='Giá',
        height=600,
        template='plotly_dark',
        xaxis_rangeslider_visible=False,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
    )
    
    # Thêm các nút điều khiển để hiển thị/ẩn các chỉ báo
    fig.update_layout(
        updatemenus=[
            dict(
                type="buttons",
                direction="right",
                buttons=list([
                    dict(
                        args=[{"visible": [True, True, True, True, True, True, True, True] if compare_ticker is None else [True, True, True, True, True, True, True, True]}],
                        label="Hiển thị tất cả",
                        method="update"
                    ),
                    dict(
                        args=[{"visible": [True, True, True, True, False, False, False, False] if compare_ticker is None else [True, True, True, True, False, False, False, True]}],
                        label="EMA",
                        method="update"
                    ),
                    dict(
                        args=[{"visible": [True, False, False, False, True, True, True, False] if compare_ticker is None else [True, False, False, False, True, True, True, True]}],
                        label="Bollinger Bands",
                        method="update"
                    ),
                    dict(
                        args=[{"visible": [True, False, False, False, False, False, False, True] if compare_ticker is not None else [True, False, False, False, False, False, False]}],
                        label="Chỉ giá",
                        method="update"
                    ),
                ]),
                pad={"r": 10, "t": 10},
                showactive=True,
                x=0.1,
                xanchor="left",
                y=1.1,
                yanchor="top"
            ),
        ]
    )
    
    return fig

# Hàm tạo biểu đồ RSI
def create_rsi_chart(df):
    """Tạo biểu đồ RSI"""
    if df.empty or 'RSI' not in df.columns:
        return go.Figure()
    
    fig = go.Figure()
    
    # Thêm đường RSI
    fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name='RSI', line=dict(color='blue', width=2)))
    
    # Thêm đường tham chiếu tại 30 và 70
    fig.add_trace(go.Scatter(x=[df.index[0], df.index[-1]], y=[30, 30], name='Quá bán', line=dict(color='green', width=1, dash='dash')))
    fig.add_trace(go.Scatter(x=[df.index[0], df.index[-1]], y=[70, 70], name='Quá mua', line=dict(color='red', width=1, dash='dash')))
    
    # Vùng nền cho khu vực quá mua/quá bán
    fig.add_trace(go.Scatter(
        x=df.index, y=[30] * len(df),
        fill=None, mode='lines', line_color='green',
        showlegend=False
    ))
    
    fig.add_trace(go.Scatter(
        x=df.index, y=[0] * len(df),
        fill='tonexty', mode='lines', line_color='green',
        fillcolor='rgba(0, 255, 0, 0.1)', showlegend=False
    ))
    
    fig.add_trace(go.Scatter(
        x=df.index, y=[70] * len(df),
        fill=None, mode='lines', line_color='red',
        showlegend=False
    ))
    
    fig.add_trace(go.Scatter(
        x=df.index, y=[100] * len(df),
        fill='tonexty', mode='lines', line_color='red',
        fillcolor='rgba(255, 0, 0, 0.1)', showlegend=False
    ))
    
    # Cấu hình hiển thị
    fig.update_layout(
        title='RSI (14)',
        xaxis_title='Thời gian',
        yaxis_title='RSI',
        height=250,
        template='plotly_dark',
        yaxis=dict(range=[0, 100]),
        showlegend=False,
    )
    
    return fig

# Hàm tạo biểu đồ MACD
def create_macd_chart(df):
    """Tạo biểu đồ MACD"""
    if df.empty or 'MACD' not in df.columns:
        return go.Figure()
    
    fig = go.Figure()
    
    # Thêm histogram cho MACD Histogram
    fig.add_trace(go.Bar(
        x=df.index, 
        y=df['MACD_Hist'], 
        name='MACD Hist',
        marker_color=np.where(df['MACD_Hist'] >= 0, 'green', 'red')
    ))
    
    # Thêm các đường MACD và Signal
    fig.add_trace(go.Scatter(x=df.index, y=df['MACD'], name='MACD', line=dict(color='blue', width=2)))
    fig.add_trace(go.Scatter(x=df.index, y=df['MACD_Signal'], name='Signal', line=dict(color='orange', width=2)))
    
    # Cấu hình hiển thị
    fig.update_layout(
        title='MACD (12, 26, 9)',
        xaxis_title='Thời gian',
        yaxis_title='MACD',
        height=250,
        template='plotly_dark',
        showlegend=False,
    )
    
    return fig

# Layout của ứng dụng
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("Phân tích cổ phiếu thời gian thực", className="text-center my-4"),
            html.P("Dữ liệu được cập nhật tự động mỗi 15 giây", className="text-center text-muted"),
        ], width=12)
    ]),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Label("Chọn mã cổ phiếu:"),
                            dcc.Dropdown(
                                id="ticker-input",
                                options=dropdown_options,
                                value="AAPL",
                                placeholder="Tìm kiếm mã cổ phiếu...",
                                searchable=True,
                                clearable=False,
                                optionHeight=60,
                                style={"width": "100%"},
                                className="dropdown-with-groups",
                            ),
                        ], width=5),
                        dbc.Col([
                            html.Label("So sánh với (tùy chọn):"),
                            dcc.Dropdown(
                                id="compare-ticker-input",
                                options=dropdown_options,
                                value=None,
                                placeholder="Chọn mã cổ phiếu để so sánh...",
                                searchable=True,
                                clearable=True,
                                optionHeight=60,
                                style={"width": "100%"},
                                className="dropdown-with-groups",
                            ),
                        ], width=5),
                        dbc.Col([
                            html.Label("Khung thời gian:"),
                            dbc.Select(
                                id="timeframe-select",
                                options=[
                                    {"label": "1 ngày", "value": "1d"},
                                    {"label": "5 ngày", "value": "5d"},
                                    {"label": "1 tháng", "value": "1mo"},
                                    {"label": "6 tháng", "value": "6mo"},
                                    {"label": "1 năm", "value": "1y"},
                                    {"label": "Từ đầu năm", "value": "ytd"},
                                    {"label": "Tối đa", "value": "max"},
                                ],
                                value="1d",
                            ),
                        ], width=2),
                    ]),
                    dbc.Row([
                        dbc.Col([], width=10),
                        dbc.Col([
                            html.Br(),
                            dbc.Button("Cập nhật", id="update-button", color="primary", className="w-100"),
                        ], width=2),
                    ])
                ])
            ], className="mb-4"),
            
            dbc.Card([
                dbc.CardBody([
                    dbc.Spinner(
                        dcc.Graph(id="price-chart", config={"displayModeBar": True}),
                        color="primary",
                    ),
                ])
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            dbc.Spinner(
                                dcc.Graph(id="rsi-chart", config={"displayModeBar": False}),
                                color="primary",
                            ),
                        ])
                    ]),
                ], width=6),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            dbc.Spinner(
                                dcc.Graph(id="macd-chart", config={"displayModeBar": False}),
                                color="primary",
                            ),
                        ])
                    ]),
                ], width=6),
            ], className="mb-4"),
            
            html.Div(id="alert-container"),
            
            # Thông tin cổ phiếu
            html.Div(id="stock-info-container", className="mb-4"),
            
            # Cài đặt cập nhật tự động
            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.H5("Cài đặt cập nhật tự động", className="mb-3"),
                            dbc.Switch(
                                id="auto-update-switch",
                                label="Bật cập nhật tự động",
                                value=True,
                                className="mb-3",
                            ),
                            html.Div(id="update-status", className="text-muted"),
                        ], width=4),
                        dbc.Col([
                            html.Label("Thời gian cập nhật (giây):"),
                            dbc.Select(
                                id="update-interval-select",
                                options=[
                                    {"label": "15 giây", "value": "15"},
                                    {"label": "30 giây", "value": "30"},
                                    {"label": "1 phút", "value": "60"},
                                    {"label": "5 phút", "value": "300"},
                                ],
                                value="60",
                            ),
                        ], width=4),
                        dbc.Col([
                            html.Br(),
                            dbc.Button(
                                "Cập nhật ngay", 
                                id="manual-update-button", 
                                color="primary", 
                                className="w-100"
                            ),
                        ], width=4),
                    ]),
                ])
            ], className="mb-4"),
            
            dcc.Interval(
                id="interval-component",
                interval=60 * 1000,  # in milliseconds (60 seconds)
                n_intervals=0,
                disabled=False,
            ),
            
            # Lưu thông tin cổ phiếu hiện tại
            dcc.Store(id="current-ticker"),
            dcc.Store(id="current-timeframe"),
            dcc.Store(id="compare-ticker"),
            
            # Thêm footer
            html.Footer([
                html.Hr(),
                html.P("Dữ liệu được cung cấp bởi Yahoo Finance qua thư viện yfinance", className="text-center text-muted"),
                html.P("© 2023 Stock Analysis App", className="text-center text-muted"),
            ], className="my-4"),
            
        ], width=12),
    ]),
], fluid=True)

# Callback để cập nhật biểu đồ khi người dùng nhập ticker mới
@app.callback(
    [
        Output("price-chart", "figure"),
        Output("rsi-chart", "figure"),
        Output("macd-chart", "figure"),
        Output("alert-container", "children"),
        Output("stock-info-container", "children"),
        Output("current-ticker", "data"),
        Output("current-timeframe", "data"),
        Output("compare-ticker", "data"),
    ],
    [
        Input("update-button", "n_clicks"),
        Input("interval-component", "n_intervals"),
        Input("manual-update-button", "n_clicks"),
    ],
    [
        State("ticker-input", "value"),
        State("compare-ticker-input", "value"),
        State("timeframe-select", "value"),
        State("current-ticker", "data"),
        State("current-timeframe", "data"),
        State("compare-ticker", "data"),
    ],
)
def update_charts(n_clicks, n_intervals, manual_update, ticker_input, compare_ticker_input, timeframe, current_ticker, current_timeframe, current_compare_ticker):
    # Xác định context của callback
    ctx = dash.callback_context
    trigger = ctx.triggered[0]["prop_id"].split(".")[0]
    
    # Nếu là interval trigger, sử dụng ticker hiện tại
    if trigger == "interval-component":
        if current_ticker:
            ticker = current_ticker
            compare_ticker = current_compare_ticker
            timeframe = current_timeframe if current_timeframe else "1d"
        else:
            ticker = ticker_input or "AAPL"
            compare_ticker = compare_ticker_input
            timeframe = timeframe or "1d"
    else:
        ticker = ticker_input or "AAPL"
        compare_ticker = compare_ticker_input
        timeframe = timeframe or "1d"
    
    # Xác định interval dựa trên timeframe
    interval = get_interval_for_timeframe(timeframe)
    
    # Lấy dữ liệu và tính toán chỉ báo
    df = get_stock_data(ticker, period=timeframe, interval=interval)
    df_compare = get_stock_data(compare_ticker, period=timeframe, interval=interval)
    df = calculate_indicators(df)
    df_compare = calculate_indicators(df_compare)
    
    # Tạo biểu đồ
    price_fig = create_chart(df, ticker, df_compare, compare_ticker)
    rsi_fig = create_rsi_chart(df)
    macd_fig = create_macd_chart(df)
    
    # Tạo cảnh báo
    alerts = generate_alerts(df)
    alert_components = []
    
    for alert in alerts:
        alert_components.append(
            dbc.Alert(
                alert["message"],
                color=alert["type"],
                dismissable=True,
                className="mb-2",
            )
        )
    
    if not alerts:
        alert_components.append(
            dbc.Alert(
                "Không có cảnh báo nào vào lúc này",
                color="info",
                dismissable=True,
                className="mb-2",
            )
        )
    
    # Tạo thông tin cơ bản về cổ phiếu
    stock_info = None
    if not df.empty:
        latest_price = df['Close'].iloc[-1]
        change = latest_price - df['Close'].iloc[-2] if len(df) > 1 else 0
        change_pct = (change / df['Close'].iloc[-2] * 100) if len(df) > 1 else 0
        
        # Định dạng thay đổi giá
        change_text = f"{change:.2f} ({change_pct:.2f}%)"
        change_color = "success" if change >= 0 else "danger"
        
        # Card chính cho cổ phiếu chính
        main_stock_card = dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.H4(f"{ticker}", className="mb-0"),
                        html.P(f"Cập nhật: {df.index[-1].strftime('%d/%m/%Y %H:%M:%S')}", className="text-muted"),
                    ]),
                    dbc.Col([
                        html.H4(f"{latest_price:.2f}", className="mb-0 text-end"),
                        html.P([
                            html.Span(change_text, className=f"text-{change_color}"),
                            html.Span(" hôm nay", className="text-muted ms-1"),
                        ], className="text-end mb-0"),
                    ]),
                ]),
                html.Hr(),
                dbc.Row([
                    dbc.Col([
                        html.P("Mở:", className="mb-0"),
                        html.H6(f"{df['Open'].iloc[-1]:.2f}"),
                    ], width=3),
                    dbc.Col([
                        html.P("Cao:", className="mb-0"),
                        html.H6(f"{df['High'].iloc[-1]:.2f}"),
                    ], width=3),
                    dbc.Col([
                        html.P("Thấp:", className="mb-0"),
                        html.H6(f"{df['Low'].iloc[-1]:.2f}"),
                    ], width=3),
                    dbc.Col([
                        html.P("Đóng:", className="mb-0"),
                        html.H6(f"{df['Close'].iloc[-1]:.2f}"),
                    ], width=3),
                ]),
                dbc.Row([
                    dbc.Col([
                        html.P("RSI:", className="mb-0"),
                        html.H6(f"{df['RSI'].iloc[-1]:.2f}"),
                    ], width=4),
                    dbc.Col([
                        html.P("MACD:", className="mb-0"),
                        html.H6(f"{df['MACD'].iloc[-1]:.2f}"),
                    ], width=4),
                    dbc.Col([
                        html.P("ATR:", className="mb-0"),
                        html.H6(f"{df['ATR'].iloc[-1]:.2f}"),
                    ], width=4),
                ]),
            ])
        ])
        
        # Nếu có cổ phiếu so sánh
        if compare_ticker_input is not None and not df_compare.empty:
            compare_latest_price = df_compare['Close'].iloc[-1]
            compare_change = compare_latest_price - df_compare['Close'].iloc[-2] if len(df_compare) > 1 else 0
            compare_change_pct = (compare_change / df_compare['Close'].iloc[-2] * 100) if len(df_compare) > 1 else 0
            
            # Định dạng thay đổi giá cho cổ phiếu so sánh
            compare_change_text = f"{compare_change:.2f} ({compare_change_pct:.2f}%)"
            compare_change_color = "success" if compare_change >= 0 else "danger"
            
            # Card cho cổ phiếu so sánh
            compare_stock_card = dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.H4(f"{compare_ticker_input}", className="mb-0"),
                            html.P(f"Cập nhật: {df_compare.index[-1].strftime('%d/%m/%Y %H:%M:%S')}", className="text-muted"),
                        ]),
                        dbc.Col([
                            html.H4(f"{compare_latest_price:.2f}", className="mb-0 text-end"),
                            html.P([
                                html.Span(compare_change_text, className=f"text-{compare_change_color}"),
                                html.Span(" hôm nay", className="text-muted ms-1"),
                            ], className="text-end mb-0"),
                        ]),
                    ]),
                    html.Hr(),
                    dbc.Row([
                        dbc.Col([
                            html.P("RSI:", className="mb-0"),
                            html.H6(f"{df_compare['RSI'].iloc[-1]:.2f}"),
                        ], width=4),
                        dbc.Col([
                            html.P("MACD:", className="mb-0"),
                            html.H6(f"{df_compare['MACD'].iloc[-1]:.2f}"),
                        ], width=4),
                        dbc.Col([
                            html.P("ATR:", className="mb-0"),
                            html.H6(f"{df_compare['ATR'].iloc[-1]:.2f}"),
                        ], width=4),
                    ]),
                ])
            ], className="mt-3")
            
            # Hiển thị cả hai card
            stock_info = html.Div([
                main_stock_card,
                compare_stock_card
            ])
        else:
            # Chỉ hiển thị card chính
            stock_info = main_stock_card
    
    return price_fig, rsi_fig, macd_fig, alert_components, stock_info, ticker, timeframe, compare_ticker

# Callback để điều khiển interval
@app.callback(
    [
        Output("interval-component", "interval"),
        Output("interval-component", "disabled"),
    ],
    [
        Input("auto-update-switch", "value"),
        Input("update-interval-select", "value"),
    ],
)
def update_interval_settings(auto_update_enabled, update_interval):
    """Cập nhật cài đặt interval dựa trên trạng thái switch và giá trị dropdown"""
    interval = int(update_interval) * 1000  # Chuyển giây sang milli giây
    disabled = not auto_update_enabled
    
    return interval, disabled

# Callback để hiển thị trạng thái cập nhật
@app.callback(
    Output("update-status", "children"),
    [
        Input("auto-update-switch", "value"),
        Input("update-interval-select", "value"),
    ],
)
def update_status_text(auto_update_enabled, update_interval):
    """Hiển thị trạng thái cập nhật dữ liệu"""
    if not auto_update_enabled:
        return "Cập nhật tự động: Đã tắt"
    
    return f"Cập nhật tự động: Kích hoạt (mỗi {update_interval}s)"

# Chạy ứng dụng
if __name__ == "__main__":
    app.run_server(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 8050)))
    
# Tạo alias 'app' cho server để gunicorn có thể sử dụng cả app:app và app:server
# Dòng này chỉ thực thi khi module được import, không phải khi chạy trực tiếp
app = server 