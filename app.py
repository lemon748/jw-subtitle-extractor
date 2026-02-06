import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from playwright.sync_api import sync_playwright

# 로그 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return jsonify({
        'status': 'active', 
        'system': 'Docker Playwright Server'
    })

@app.route('/convert', methods=['POST'])
def convert_subtitle():
    try:
        data = request.json
        video_url = data.get('url')
        language = data.get('language', 'KO')
        
        logger.info(f"요청 받음: {video_url}")

        if not video_url:
            return jsonify({'error': 'URL이 없습니다.'}), 400

        # 브라우저 실행
        with sync_playwright() as p:
            # headless=True는 화면 없이 실행한다는 뜻
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
            page = context.new_page()

            # 사이트 접속
            logger.info("사이트 접속 중...")
            page.goto('https://subtitle-c2419.firebaseapp.com/ko/', timeout=60000)
            
            # 페이지 로딩 대기
            page.wait_for_load_state("networkidle")

            # 언어 선택
            page.select_option('#languages', language)
            
            # URL 입력
            page.fill('#url-input', video_url)
            
            # Paste 버튼 클릭 (입력 인식용)
            if page.is_visible('button:has-text("Paste")'):
                page.click('button:has-text("Paste")')

            # Submit 버튼 활성화 대기 및 클릭
            # 버튼이 활성화(disabled가 없어짐)될 때까지 기다림
            submit_selector = 'button.button:not([disabled])'
            page.wait_for_selector(submit_selector, timeout=10000)
            
            # Submit 클릭
            logger.info("변환 버튼 클릭")
            page.click(submit_selector)

            # 결과 나올 때까지 대기 (최대 60초)
            logger.info("결과 기다리는 중...")
            result_selector = '#result-textarea:not([disabled])'
            page.wait_for_selector(result_selector, timeout=60000)
            
            # 텍스트 추출
            subtitle_text = page.inner_text('#result-textarea')
            
            browser.close()

            if subtitle_text:
                return jsonify({'success': True, 'subtitle': subtitle_text})
            else:
                return jsonify({'success': False, 'error': '자막이 비어있습니다.'}), 500

    except Exception as e:
        logger.error(f"에러 발생: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    # Render는 포트 10000을 주로 사용합니다
    app.run(host='0.0.0.0', port=10000)
