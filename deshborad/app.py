"""
حلالية - لوحة التحكم الاحترافية
Dashboard Pro for Halalia Platform
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import plotly.express as px
from backend.db import db

# ==========================================
# إعدادات الصفحة
# ==========================================
st.set_page_config(
    page_title="حلالية - لوحة التحكم",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# CSS مخصص
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700&display=swap');
    
    * {
        font-family: 'Tajawal', sans-serif;
    }
    
    .main-header {
        background: linear-gradient(135deg, #2d5016 0%, #4a7c23 50%, #6b9b37 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .main-header h1 {
        font-size: 2.5rem;
        margin: 0;
        color: white;
    }
    
    .main-header p {
        font-size: 1.1rem;
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
    }
    
    .section-title {
        background: #f8f9fa;
        padding: 1rem 1.5rem;
        border-radius: 10px;
        border-right: 5px solid #4a7c23;
        margin: 2rem 0 1rem 0;
    }
    
    .section-title h2 {
        margin: 0;
        color: #2d5016;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# جلب البيانات
# ==========================================
@st.cache_data(ttl=60)
def load_all_products():
    try:
        query = """
            SELECT id, product_name, score, hunter_score, rank, recommendation, 
                   sell_price, rating, reviews_count, demand, competition, niche, 
                   halal_status, created_at
            FROM products 
            ORDER BY created_at DESC
        """
        results = db.execute_query(query, fetch=True)
        if results:
            df = pd.DataFrame([dict(row) for row in results])

            # ✅ تحويل الأعمدة إلى أنواعها الصحيحة
            df['rating'] = pd.to_numeric(df['rating'], errors='coerce').fillna(0)
            df['score'] = pd.to_numeric(df['score'], errors='coerce').fillna(0)
            df['sell_price'] = pd.to_numeric(df['sell_price'], errors='coerce').fillna(0)
            df['reviews_count'] = pd.to_numeric(df['reviews_count'], errors='coerce').fillna(0)
            df['hunter_score'] = pd.to_numeric(df['hunter_score'], errors='coerce').fillna(0)

            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"خطأ في جلب البيانات: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=60)
def load_stats():
    try:
        stats = {}

        total = db.execute_query("SELECT COUNT(*) as count FROM products", fetch=True)
        stats['total'] = total[0]['count'] if total else 0

        avg = db.execute_query("SELECT AVG(rating) as avg FROM products WHERE rating > 0", fetch=True)
        stats['avg_rating'] = avg[0]['avg'] if avg and avg[0]['avg'] else 0

        # ✅ التحقق من القيم الفعلية لـ halal_status
        halal = db.execute_query("SELECT COUNT(*) as count FROM products WHERE halal_status = 'halal'", fetch=True)
        stats['halal'] = halal[0]['count'] if halal else 0

        high = db.execute_query("SELECT COUNT(*) as count FROM products WHERE score >= 7", fetch=True)
        stats['high_score'] = high[0]['count'] if high else 0

        reviews = db.execute_query("SELECT SUM(reviews_count) as total FROM products", fetch=True)
        stats['total_reviews'] = reviews[0]['total'] if reviews and reviews[0]['total'] else 0

        avg_price = db.execute_query("SELECT AVG(sell_price) as avg FROM products WHERE sell_price > 0", fetch=True)
        stats['avg_price'] = avg_price[0]['avg'] if avg_price and avg_price[0]['avg'] else 0

        return stats
    except Exception as e:
        st.error(f"خطأ في الإحصائيات: {e}")
        return {}


# تحميل البيانات
df = load_all_products()
stats = load_stats()

# ==========================================
# الهيدر الرئيسي
# ==========================================
st.markdown("""
<div class="main-header">
    <h1>🌸 حلالية - لوحة التحكم الاحترافية</h1>
    <p>منصة الذكاء الاصطناعي الحلال للمتسوقات</p>
</div>
""", unsafe_allow_html=True)

# ==========================================
# الشريط الجانبي - الفلاتر
# ==========================================
with st.sidebar:
    st.markdown("### 🎛️ الفلاتر والبحث")
    st.markdown("---")

    search_query = st.text_input("🔍 ابحث عن منتج:", placeholder="اكتب اسم المنتج...")

    if not df.empty:
        niches = ['الكل'] + sorted(df['niche'].dropna().unique().tolist())
        selected_niche = st.selectbox("📂 الفئة:", niches)
    else:
        selected_niche = 'الكل'

    halal_filter = st.selectbox(
        "✅ حالة الحلال:",
        ['الكل', 'halal', 'doubtful', 'haram', 'unknown'],
        format_func=lambda x: {
            'الكل': 'جميع الحالات',
            'halal': '🟢 حلال',
            'doubtful': '🟡 يحتاج تحقق',
            'haram': '🔴 غير حلال',
            'unknown': ' غير محدد'
        }.get(x, x)
    )

    score_range = st.slider(
        "📊 نطاق درجة الثقة:",
        min_value=0,
        max_value=10,
        value=(0, 10)
    )

    rating_filter = st.selectbox(
        "⭐ التقييم:",
        ['الكل', 'ممتاز (4.5+)', 'جيد (3.5-4.4)', 'متوسط (2.5-3.4)', 'ضعيف (<2.5)']
    )

    st.markdown("---")
    st.markdown("### 📊 معلومات سريعة")
    st.info(f"📦 إجمالي المنتجات: {stats.get('total', 0)}")
    st.info(f"✅ منتجات حلال: {stats.get('halal', 0)}")
    st.info(f"⭐ متوسط التقييم: {stats.get('avg_rating', 0):.1f}/5")

# ==========================================
# تطبيق الفلاتر
# ==========================================
filtered_df = df.copy()

if search_query:
    filtered_df = filtered_df[filtered_df['product_name'].str.contains(search_query, case=False, na=False)]

if selected_niche != 'الكل':
    filtered_df = filtered_df[filtered_df['niche'] == selected_niche]

if halal_filter != 'الكل':
    filtered_df = filtered_df[filtered_df['halal_status'] == halal_filter]

filtered_df = filtered_df[
    (filtered_df['score'] >= score_range[0]) &
    (filtered_df['score'] <= score_range[1])
]

if rating_filter != 'الكل':
    if rating_filter == 'ممتاز (4.5+)':
        filtered_df = filtered_df[filtered_df['rating'] >= 4.5]
    elif rating_filter == 'جيد (3.5-4.4)':
        filtered_df = filtered_df[(filtered_df['rating'] >= 3.5) & (filtered_df['rating'] < 4.5)]
    elif rating_filter == 'متوسط (2.5-3.4)':
        filtered_df = filtered_df[(filtered_df['rating'] >= 2.5) & (filtered_df['rating'] < 3.5)]
    elif rating_filter == 'ضعيف (<2.5)':
        filtered_df = filtered_df[filtered_df['rating'] < 2.5]

# ==========================================
# الإحصائيات السريعة
# ==========================================
st.markdown('<div class="section-title"><h2>📊 الإحصائيات السريعة</h2></div>', unsafe_allow_html=True)

col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    st.metric("📦 إجمالي المنتجات", stats.get('total', 0))
with col2:
    st.metric("✅ منتجات حلال", stats.get('halal', 0))
with col3:
    st.metric("⭐ متوسط التقييم", f"{stats.get('avg_rating', 0):.1f}/5")
with col4:
    st.metric("🏆 عالية الثقة", stats.get('high_score', 0))
with col5:
    st.metric("💬 إجمالي التقييمات", f"{stats.get('total_reviews', 0):,}")
with col6:
    st.metric("💰 متوسط السعر", f"${stats.get('avg_price', 0):.0f}")

# ==========================================
# الرسوم البيانية
# ==========================================
st.markdown('<div class="section-title"><h2>📈 التحليلات البصرية</h2></div>', unsafe_allow_html=True)

if not filtered_df.empty:
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.markdown("#### 🥧 توزيع حالة الحلال")
        halal_counts = filtered_df['halal_status'].value_counts()

        if not halal_counts.empty:
            labels_map = {
                'halal': 'حلال',
                'doubtful': 'يحتاج تحقق',
                'haram': 'غير حلال',
                'unknown': 'غير محدد'
            }
            colors_map = {
                'halal': '#28a745',
                'doubtful': '#ffc107',
                'haram': '#dc3545',
                'unknown': '#6c757d'
            }

            fig_pie = px.pie(
                values=halal_counts.values,
                names=[labels_map.get(k, k) for k in halal_counts.index],
                color=[labels_map.get(k, k) for k in halal_counts.index],
                color_discrete_map={v: colors_map.get(k, '#999') for k, v in zip(halal_counts.index, [labels_map.get(k, k) for k in halal_counts.index])},
                hole=0.4
            )
            fig_pie.update_layout(height=400, font=dict(family='Tajawal', size=12))
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("لا توجد بيانات كافية")

    with chart_col2:
        st.markdown("#### 📊 توزيع التقييمات")
        rating_dist = filtered_df[filtered_df['rating'] > 0]['rating'].value_counts().sort_index()

        if not rating_dist.empty:
            fig_bar = px.bar(
                x=rating_dist.index,
                y=rating_dist.values,
                labels={'x': 'التقييم', 'y': 'عدد المنتجات'},
                color=rating_dist.values,
                color_continuous_scale='Greens'
            )
            fig_bar.update_layout(
                height=400,
                font=dict(family='Tajawal', size=12),
                xaxis_title='التقييم (من 5)',
                yaxis_title='عدد المنتجات'
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("لا توجد تقييمات كافية")

    chart_col3, chart_col4 = st.columns(2)

    with chart_col3:
        st.markdown("#### 📂 توزيع الفئات (Niche)")
        niche_counts = filtered_df['niche'].value_counts()

        if not niche_counts.empty:
            fig_niche = px.bar(
                x=niche_counts.values,
                y=niche_counts.index,
                orientation='h',
                labels={'x': 'العدد', 'y': 'الفئة'},
                color=niche_counts.values,
                color_continuous_scale='YlGn'
            )
            fig_niche.update_layout(
                height=400,
                font=dict(family='Tajawal', size=12),
                yaxis={'categoryorder': 'total ascending'}
            )
            st.plotly_chart(fig_niche, use_container_width=True)
        else:
            st.info("لا توجد بيانات كافية")

    with chart_col4:
        st.markdown("#### 🎯 توزيع درجة الثقة (Score)")
        score_bins = [0, 3, 5, 7, 10]
        score_labels = ['ضعيف (0-3)', 'متوسط (3-5)', 'جيد (5-7)', 'ممتاز (7-10)']
        filtered_df['score_category'] = pd.cut(filtered_df['score'], bins=score_bins, labels=score_labels, right=False)
        score_dist = filtered_df['score_category'].value_counts()

        if not score_dist.empty:
            fig_score = px.pie(
                values=score_dist.values,
                names=score_dist.index,
                hole=0.4,
                color=score_dist.index,
                color_discrete_map={
                    'ضعيف (0-3)': '#dc3545',
                    'متوسط (3-5)': '#ffc107',
                    'جيد (5-7)': '#17a2b8',
                    'ممتاز (7-10)': '#28a745'
                }
            )
            fig_score.update_layout(height=400, font=dict(family='Tajawal', size=12))
            st.plotly_chart(fig_score, use_container_width=True)
        else:
            st.info("لا توجد بيانات كافية")
else:
    st.warning("️ لا توجد منتجات مطابقة للفلاتر المحددة")

# ==========================================
# عرض تفاصيل المنتج
# ==========================================
st.markdown('<div class="section-title"><h2>🔍 عرض تفاصيل المنتج</h2></div>', unsafe_allow_html=True)

if not filtered_df.empty:
    product_names = filtered_df['product_name'].tolist()
    selected_product = st.selectbox("اختر منتجاً لعرض تفاصيله:", product_names)

    if selected_product:
        product_data = filtered_df[filtered_df['product_name'] == selected_product].iloc[0]

        detail_col1, detail_col2 = st.columns(2)

        with detail_col1:
            st.markdown("### 📋 المعلومات الأساسية")
            st.markdown(f"""
            - **الاسم:** {product_data['product_name']}
            - **الدرجة:** {product_data['score']}/10
            - **التقييم:** {product_data['rating']}/5 ⭐
            - **عدد التقييمات:** {int(product_data['reviews_count']):,}
            - **السعر:** ${product_data['sell_price']}
            """)

            st.markdown("### ✅ حالة الحلال")
            halal_status = product_data.get('halal_status', 'unknown')
            halal_emoji = {
                'halal': '🟢 حلال',
                'doubtful': '🟡 يحتاج تحقق',
                'haram': '🔴 غير حلال',
                'unknown': '⚪ غير محدد'
            }.get(halal_status, '⚪ غير محدد')
            st.markdown(f"**الحالة:** {halal_emoji}")

        with detail_col2:
            st.markdown("### 📊 تحليل السوق")
            st.markdown(f"""
            - **الطلب:** {product_data.get('demand', 'N/A')}
            - **المنافسة:** {product_data.get('competition', 'N/A')}
            - **الفئة:** {product_data.get('niche', 'N/A')}
            - **الترتيب:** {product_data.get('rank', 'N/A')}
            """)

            st.markdown("### 💡 التوصية")
            st.info(product_data.get('recommendation', 'لا توجد توصية'))

# ==========================================
# الجداول
# ==========================================
st.markdown('<div class="section-title"><h2> عرض البيانات</h2></div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🆕 أحدث المنتجات", " جميع المنتجات", "🔥 الأعلى تقييماً"])

with tab1:
    st.markdown("#### أحدث 10 منتجات مضافة")
    if not filtered_df.empty:
        latest = filtered_df.head(10)[['product_name', 'score', 'rating', 'sell_price', 'halal_status', 'created_at']]
        st.dataframe(latest, width='stretch', hide_index=True)
    else:
        st.info("لا توجد منتجات")

with tab2:
    st.markdown(f"#### جميع المنتجات ({len(filtered_df)} منتج)")
    if not filtered_df.empty:
        st.dataframe(filtered_df, width='stretch', hide_index=True)
    else:
        st.info("لا توجد منتجات")

with tab3:
    st.markdown("#### الأعلى تقييماً (Rating)")
    if not filtered_df.empty:
        rated_df = filtered_df[filtered_df['rating'] > 0]
        if not rated_df.empty:
            top_rated = rated_df.nlargest(10, 'rating')
            st.dataframe(top_rated[['product_name', 'rating', 'reviews_count', 'score', 'sell_price']],
                        width='stretch', hide_index=True)
        else:
            st.info("لا توجد منتجات مقيّمة")
    else:
        st.info("لا توجد منتجات")

# ==========================================
# التذييل
# ==========================================
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 2rem; background: linear-gradient(135deg, #2d5016 0%, #4a7c23 100%); 
            border-radius: 15px; color: white; margin-top: 2rem;">
    <h3 style="margin: 0;">🌸 حلالية</h3>
    <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">منصة الذكاء الاصطناعي الحلال للمتسوقات</p>
    <p style="margin: 0.5rem 0 0 0; font-size: 0.9rem; opacity: 0.7;">© 2026 جميع الحقوق محفوظة</p>
</div>
""", unsafe_allow_html=True)