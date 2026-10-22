
import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date, timedelta

# =========================
# 1. CẤU HÌNH ỨNG DỤNG
# =========================
st.set_page_config(
    page_title="Stock Chart Vietnam",
    page_icon="📈",
    layout="wide"
)

# Giao diện
st.markdown("""
<style>
    .main-title {
        font-size: 32px;
        font-weight: 800;
        color: #2563eb;
    }
    .subtitle {
        color: #64748b;
        font-size: 15px;
    }
    div[data-testid="stMetric"] {
        background-color: rgba(128,128,128,0.08);
        padding: 16px;
        border-radius: 12px;
        border: 1px solid rgba(128,128,128,0.15);
    }
</style>
""", unsafe_allow_html=True)

st.markdown(
    '<div class="main-title">📈 VIETNAM STOCK CHART</div>',
    unsafe_allow_html=True
)
st.markdown(
    '<div class="subtitle">Theo dõi lịch sử giá cổ phiếu Việt Nam</div>',
    unsafe_allow_html=True
)

st.divider()


# =========================
# 2. TẢI DỮ LIỆU CỔ PHIẾU
# =========================
@st.cache_data(ttl=300, show_spinner=False)
def get_stock_data(symbol, start_date, end_date):
    """
    Lấy dữ liệu lịch sử từ Yahoo Finance.
    Yahoo Finance sử dụng hậu tố .VN cho nhiều mã
    cổ phiếu niêm yết tại Việt Nam.
    """

    ticker = f"{symbol.upper()}.VN"

    # end của yfinance không bao gồm ngày kết thúc,
    # do đó cần cộng thêm một ngày.
    end_exclusive = (
        pd.Timestamp(end_date) + pd.Timedelta(days=1)
    )

    data = yf.download(
        ticker,
        start=start_date.isoformat(),
        end=end_exclusive.strftime("%Y-%m-%d"),
        interval="1d",
        auto_adjust=False,
        progress=False,
        threads=False,
        timeout=20
    )

    if data is None or data.empty:
        return pd.DataFrame()

    # Xử lý trường hợp yfinance trả về MultiIndex
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    if "Close" not in data.columns:
        return pd.DataFrame()

    # Chỉ giữ các cột cần thiết
    columns = [
        col for col in
        ["Open", "High", "Low", "Close", "Volume"]
        if col in data.columns
    ]

    data = data[columns].copy()
    data.index = pd.to_datetime(data.index)

    # Bỏ dữ liệu không có giá đóng cửa
    data = data.dropna(subset=["Close"])
    data = data.sort_index()

    return data


# =========================
# 3. NHẬP THÔNG TIN
# =========================
st.subheader("🔎 Tra cứu cổ phiếu")

with st.form("stock_search_form"):
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        symbol = st.text_input(
            "Mã cổ phiếu",
            value="VNM",
            max_chars=10,
            help="Ví dụ: VNM, FPT, HPG, VCB"
        ).strip().upper()

    with col2:
        start_date = st.date_input(
            "Ngày bắt đầu",
            value=date(2020, 1, 1),
            min_value=date(2000, 1, 1),
            max_value=date.today()
        )

    with col3:
        end_date = st.date_input(
            "Ngày kết thúc",
            value=date.today(),
            min_value=date(2000, 1, 1),
            max_value=date.today()
        )

    submitted = st.form_submit_button(
        "📊 VẼ ĐỒ THỊ",
        type="primary",
        use_container_width=True
    )


# =========================
# 4. XỬ LÝ VÀ VẼ BIỂU ĐỒ
# =========================
if submitted:

    if not symbol:
        st.error("Vui lòng nhập mã cổ phiếu.")

    elif not symbol.isalnum():
        st.error("Mã cổ phiếu chỉ được chứa chữ cái và chữ số.")

    elif start_date > end_date:
        st.error("Ngày bắt đầu phải trước hoặc bằng ngày kết thúc.")

    else:
        try:
            with st.spinner(
                f"Đang tải dữ liệu cổ phiếu {symbol}..."
            ):
                closing_prices = get_stock_data(
                    symbol,
                    start_date,
                    end_date
                )

            if closing_prices.empty:
                st.error(
                    f"Không tìm thấy dữ liệu cho {symbol} "
                    "trong khoảng thời gian đã chọn."
                )
                st.info(
                    "Hãy kiểm tra mã cổ phiếu, thử lại sau "
                    "hoặc kiểm tra khả năng cung cấp dữ liệu "
                    "của Yahoo Finance."
                )

            else:
                # -------------------------
                # Giá gần nhất trong dữ liệu
                # -------------------------
                latest = closing_prices.iloc[-1]
                latest_date = closing_prices.index[-1]

                latest_close = float(latest["Close"])

                if len(closing_prices) >= 2:
                    previous_close = float(
                        closing_prices.iloc[-2]["Close"]
                    )

                    change = latest_close - previous_close

                    change_pct = (
                        change / previous_close * 100
                        if previous_close != 0
                        else 0
                    )
                else:
                    change = None
                    change_pct = None

                st.success(
                    f"Đã tải {len(closing_prices)} phiên dữ liệu "
                    f"của {symbol}."
                )

                st.subheader(
                    f"📌 Thông tin cổ phiếu {symbol}"
                )

                # -------------------------
                # Các thẻ thông tin
                # -------------------------
                m1, m2, m3, m4 = st.columns(4)

                m1.metric(
                    "Giá đóng cửa gần nhất",
                    f"{latest_close:,.2f}",
                    help="Giá của phiên gần nhất có dữ liệu "
                         "trong khoảng thời gian đã chọn."
                )

                m2.metric(
                    "Ngày giao dịch",
                    latest_date.strftime("%d/%m/%Y")
                )

                if change is not None:
                    m3.metric(
                        "Thay đổi so với phiên trước",
                        f"{change:+,.2f}",
                        delta=f"{change_pct:+.2f}%"
                    )
                else:
                    m3.metric(
                        "Thay đổi so với phiên trước",
                        "Chưa đủ dữ liệu"
                    )

                m4.metric(
                    "Số phiên giao dịch",
                    f"{len(closing_prices):,}"
                )

                st.caption(
                    "Lưu ý: Giá hiển thị theo đơn vị do Yahoo Finance "
                    "trả về. Hãy đối chiếu đơn vị giá với nguồn dữ liệu "
                    "trước khi sử dụng. Giá gần nhất ở đây là phiên "
                    "mới nhất có dữ liệu trong khoảng ngày đã chọn, "
                    "không nhất thiết là giá đang giao dịch."
                )

                st.divider()

                # -------------------------
                # Biểu đồ giá đóng cửa
                # -------------------------
                st.subheader(
                    f"📈 Biểu đồ giá đóng cửa {symbol}"
                )

                fig, ax = plt.subplots(figsize=(14, 6))

                ax.plot(
                    closing_prices.index,
                    closing_prices["Close"],
                    color="#2563eb",
                    linewidth=1.7,
                    label=f"Giá đóng cửa {symbol}"
                )

                # Đánh dấu giá gần nhất
                ax.scatter(
                    [latest_date],
                    [latest_close],
                    color="#ef4444",
                    s=65,
                    zorder=5,
                    label=f"Phiên gần nhất: {latest_close:,.2f}"
                )

                ax.set_title(
                    f"Biến động giá đóng cửa {symbol} "
                    f"({start_date.strftime('%d/%m/%Y')} - "
                    f"{end_date.strftime('%d/%m/%Y')})",
                    fontsize=14,
                    fontweight="bold",
                    pad=15
                )

                ax.set_xlabel("Thời gian", fontsize=11)
                ax.set_ylabel(
                    "Giá đóng cửa (theo dữ liệu nguồn)",
                    fontsize=11
                )

                ax.grid(
                    True,
                    linestyle="--",
                    alpha=0.35
                )

                ax.legend(loc="upper left")
                fig.autofmt_xdate()
                fig.tight_layout()

                st.pyplot(fig, use_container_width=True)
                plt.close(fig)

                # -------------------------
                # Bảng dữ liệu lịch sử
                # -------------------------
                st.divider()
                st.subheader("📋 Bảng giá lịch sử")

                history = closing_prices.copy()
                history.index = history.index.strftime(
                    "%d/%m/%Y"
                )
                history.index.name = "Ngày giao dịch"

                # Đổi tên cột sang tiếng Việt
                history = history.rename(
                    columns={
                        "Open": "Giá mở cửa",
                        "High": "Giá cao nhất",
                        "Low": "Giá thấp nhất",
                        "Close": "Giá đóng cửa",
                        "Volume": "Khối lượng"
                    }
                )

                # Mặc định hiển thị phiên mới nhất trước
                history = history.sort_index(ascending=False)

                st.dataframe(
                    history.style.format(
                        {
                            col: "{:,.2f}"
                            for col in history.columns
                            if col != "Khối lượng"
                        }
                        | {
                            col: "{:,.0f}"
                            for col in history.columns
                            if col == "Khối lượng"
                        }
                    ),
                    use_container_width=True,
                    height=400
                )

                # -------------------------
                # Tải dữ liệu CSV
                # -------------------------
                csv_data = closing_prices.to_csv(
                    index_label="Date"
                ).encode("utf-8-sig")

                st.download_button(
                    label="⬇️ Tải dữ liệu lịch sử CSV",
                    data=csv_data,
                    file_name=f"{symbol}_lich_su_gia.csv",
                    mime="text/csv"
                )

                st.caption(
                    "Nguồn dữ liệu: Yahoo Finance | "
                    "Thời điểm truy xuất: "
                    + pd.Timestamp.now().strftime(
                        "%d/%m/%Y %H:%M:%S"
                    )
                )

        except Exception as e:
            st.error(
                "Không thể tải hoặc xử lý dữ liệu cổ phiếu."
            )
            st.caption(
                f"Chi tiết lỗi: {type(e).__name__}: {e}"
            )
            st.info(
                "Hãy kiểm tra kết nối Internet, mã cổ phiếu "
                "và thử lại sau."
            )

else:
    st.info(
        "Nhập mã cổ phiếu, chọn ngày bắt đầu và ngày kết thúc, "
        "sau đó nhấn **VẼ ĐỒ THỊ** để xem kết quả."
    )

    st.markdown("**Ví dụ mã cổ phiếu:** `VNM` · `FPT` · `HPG` · `VCB`")
