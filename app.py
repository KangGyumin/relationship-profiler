import os
import gradio as gr
from analyzer import RelationshipAnalyzer

def analyze_pasted_text(chat_text):
    if not chat_text or len(chat_text.strip()) < 10:
        return (
            "<div style='color:#DC2626; font-size:15px; padding:12px;'>❌ 분석할 대화 내용을 10자 이상 입력해주세요.</div>",
            ""
        )
    success, result_html, raw_report = RelationshipAnalyzer.analyze(chat_text)
    return result_html, raw_report

def handle_followup_chat(user_msg, chat_history, raw_report):
    if not user_msg or not user_msg.strip():
        return "", chat_history
    
    history = list(chat_history) if chat_history else []
    if not raw_report:
        history.append({"role": "user", "content": user_msg})
        history.append({"role": "assistant", "content": "먼저 왼쪽에서 대화 분석을 진행해야 그 결과를 바탕으로 조언해줄 수 있어!"})
        return "", history
    
    bot_reply = RelationshipAnalyzer.consult_followup(raw_report, user_msg, history)
    history.append({"role": "user", "content": user_msg})
    history.append({"role": "assistant", "content": bot_reply})
    return "", history

custom_css = """
body, input, textarea, button { font-family: 'Pretendard', sans-serif !important; }
.gradio-container { max-width: 1050px !important; margin: auto !important; }
"""

with gr.Blocks(title="관계 역학 & 대화 행동 프로파일러") as demo:
    raw_report_state = gr.State("")

    gr.Markdown("## ⚡ 관계 역학 & 대화 행동 프로파일러")
    gr.Markdown("대화 맥락과 심리를 정밀 진단하고, 분석 결과를 바탕으로 AI와 1:1 실시간 추가 상담을 진행할 수 있습니다.")

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 📝 대화 내용 입력")
            input_box = gr.Textbox(
                label="카카오톡 대화 데이터",
                placeholder="카카오톡 대화방에서 복사한 대화 텍스트를 여기에 붙여넣으세요.",
                lines=14,
                value=""
            )
            btn_direct = gr.Button("🚀 관계 역학 및 대화 행동 분석", variant="primary")

        with gr.Column(scale=1):
            gr.Markdown("### 📊 분석 리포트")
            output_html = gr.HTML(
                value="<div style='color:#94A3B8; text-align:center; padding:60px 0;'>대화를 입력하고 분석 버튼을 누르면 5단계 카드 리포트가 출력됩니다.</div>"
            )

            gr.Markdown("---")
            gr.Markdown("### 🤖 프로파일러 1:1 추가 상담")
            chatbot = gr.Chatbot(label="분석 기반 후속 조언 챗봇", height=300)
            with gr.Row():
                chat_input = gr.Textbox(
                    show_label=False,
                    placeholder="리포트에 대해 궁금한 점이나 다음 대화 전략을 물어보세요 (예: '지금 선톡해도 돼?')",
                    scale=4
                )
                btn_send = gr.Button("전송", variant="primary", scale=1)

    btn_direct.click(fn=analyze_pasted_text, inputs=input_box, outputs=[output_html, raw_report_state])
    btn_send.click(fn=handle_followup_chat, inputs=[chat_input, chatbot, raw_report_state], outputs=[chat_input, chatbot])
    chat_input.submit(fn=handle_followup_chat, inputs=[chat_input, chatbot, raw_report_state], outputs=[chat_input, chatbot])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    demo.queue().launch(server_name="0.0.0.0", server_port=port)