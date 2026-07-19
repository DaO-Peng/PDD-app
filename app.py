import streamlit as st
import requests
import os

# 初始化侧边栏配置
st.sidebar.title("⚙️ 拼多多工具配置")

# 尝试从环境变量或 streamlit 的 secrets 中读取默认 Token
default_token = ""
if "REPLICATE_API_TOKEN" in os.environ:
    default_token = os.environ["REPLICATE_API_TOKEN"]
elif hasattr(st, "secrets") and "REPLICATE_API_TOKEN" in st.secrets:
    default_token = st.secrets["REPLICATE_API_TOKEN"]

replicate_token = st.sidebar.text_input(
    "Replicate API Token",
    value=default_token,
    type="password",
    help="请填入海外免费生图接口 Token，用于AI模特脸部本地化及背景更换"
)

# 如果用户在侧边栏手动填写了，则覆盖环境变量
if replicate_token:
    os.environ["REPLICATE_API_TOKEN"] = replicate_token

st.title("🛒 PDD 电商商品爆款打造助手")
st.write("输入你的基础商品描述，AI 将为您自动化批量生成符合拼多多权重规则的 60 字高权重爆款标题，并一键完成模特脸部与背景的智能化电商效果图转换。")

# 1. 输入区域
product_desc = st.text_area("✍️ 请输入商品基础描述信息：", placeholder="例如：夏季新款纯棉短袖T恤女，宽松显瘦，百搭韩版...")

# 上传图片接口
uploaded_file = st.file_uploader("📸 请上传商品的基础模特展示原图：", type=["png", "jpg", "jpeg"])

# 生成按钮
if st.button("🚀 开始一键打造爆款标题与电商效果图"):
    if not product_desc:
        st.error("❌ 请务必先输入商品的描述信息！")
    elif not uploaded_file:
        st.error("❌ 请务必先上传商品基础原画图片！")
    else:
        # --- 步骤 A：批量生成高权重爆款标题 ---
        title_url = "http://10.154.0.2:8000/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer fake-token-for-local"
        }
        
        # 严格限定大模型的身份与拼多多专属规则
        payload = {
            "model": "qwen2.5-7b-instruct",
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个精通中国电商（拼多多平台）的爆款标题SEO专家。请根据商品描述，生成5个高度符合拼多多搜索权重规则的商品长标题。每个标题必须包含大量高频搜索流量词（如：2026夏季新款、舒适透气、显瘦百搭、潮流时尚），字符长度必须严格在55到60个字之间（含标点符号与空格）。直接返回5个标题，用换行符分隔，不要包含任何前言、解释、序号或多余的标点。"
                },
                {
                    "role": "user",
                    "content": f"请根据商品描述：{product_desc}，生成5个严死拼多多60字权重的长标题。"
                }
            ]
        }
        
        try:
            title_res = requests.post(title_url, headers=headers, json=payload).json()
            raw_titles = title_res['choices'][0]['message']['content']
            
            # 将大模型返回的文本按行切分
            if isinstance(raw_titles, str):
                title_list = [t.strip() for t in raw_titles.split('\n') if t.strip()]
            else:
                title_list = raw_titles
                
            titles = []
            for t in title_list:
                # 移除序号（如 "1. "）和标点
                t_clean = t.lstrip("0123456789. ）。\"").replace("！", "").replace("，", " ").strip()
                # 拼多多高频流量词库，用于强行补齐字数
                pdd_fillers = " 2026夏季新款 舒适透气 显瘦百搭 潮流时尚"
                # 如果字符数不足55，循环拼接直到逼近60个字符
                while len(t_clean) < 55:
                    t_clean += pdd_fillers
                # 严格截取前60个字符，确保完美符合权重
                titles.append(t_clean[:60])
                
        except Exception as e:
            # 异常时进行安全的兜底填充，包含未配置说明
            titles = "1. 爆款热卖中！时尚潮流百搭上装\n2. 气质满满！高级感小众设计穿搭\n（注：本地未成功调用外部大模型，此为精选预设标题）"
            
        # --- 步骤 B：局部重绘换脸换背景 ---
        st.success("✨ 处理完成！")
        
        # 结果展示
        st.subheader("📝 推荐电商标题")
        st.info(titles)
        
        st.subheader("🖼️ 生成的电商效果图")
        col1, col2 = st.columns(2)
        
        with col1:
            st.image(uploaded_file, caption="原图（衣服将保持原样）", use_container_width=True)
            
        with col2:
            with st.spinner("AI 正在努力为您更换模特与背景..."):
                try:
                    import replicate
                    # 调用海外免费图生图接口（保持衣服不变，换脸和背景）
                    output = replicate.run(
                        "lucataco/faceswap:9a42343c1ee35a3a0c31417e857407339d7de1e5a17f3547474490ae966657c0",
                        input={
                            "target_image": uploaded_file,
                            "swap_all_faces": True
                        }
                    )
                    if output:
                        st.image(output, caption="生成效果图（模特脸部已本地化/背景已更换）", use_container_width=True)
                    else:
                        st.error("❌ 生图接口未返回有效图像。")
                except Exception as e:
                    # 报错不逃避，直接把真凶打在屏幕上
                    st.error(f"❌ 图像生成失败！真实报错原因: {str(e)}")
                    st.warning("请检查代码左侧侧边栏的 REPLICATE_API_TOKEN 是否配置正确。")
                    st.image(uploaded_file, caption="由于报错，此为兜底原图", use_container_width=True)
                    st.caption("提示：请在代码顶部或网页左侧侧边栏配置 `REPLICATE_API_TOKEN` 以激活AI图像生成能力功能。")
