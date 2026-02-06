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
    return "Server is running!"

@app.route('/convert', methods=['POST'])
def convert_subtitle():
    try:
        data = request.json
        video_url = data.get('url')
        language = data.get('language', 'KO')
        
        logger.info(f"요청 받음: {video_url}")

        if not video_url:
            return jsonify({'error': 'URL이 없습니다.'}), 400

        with sync_playwright() as p:
            # 브라우저 실행 (가볍고 빠르게)
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-gpu',
                    '--disable-extensions',
                    '--disable-images'  # 이미지 로딩 차단 (속도 향상)
                ]
            )
            context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
            page = context.new_page()

            # 타임아웃 60초 설정
            page.set_default_timeout(60000)

            logger.info("사이트 접속 중...")
            # ★ 핵심: domcontentloaded 사용 (이미지/스타일 로딩 안 기다림 -> 2배 빠름)
            page.goto('https://subtitle-c2419.firebaseapp.com/ko/', wait_until='domcontentloaded')
            
            # 언어 선택
            page.select_option('#languages', language)
            
            # URL 입력
            page.fill('#url-input', video_url)
            
            # Paste 버튼 클릭 (있으면)
            if page.is_visible('button:has-text("Paste")'):
                page.click('button:has-text("Paste")')

            # 변환 버튼 활성화 대기 (최대 10초)
            submit_selector = 'button.button:not([disabled])'
            try:
                page.wait_for_selector(submit_selector, timeout=10000)
                logger.info("변환 버튼 클릭")
                page.click(submit_selector)
            except:
                # 버튼이 안 눌리면 엔터키 시도
                page.keyboard.press('Enter')

            # 결과 대기
            logger.info("결과 기다리는 중...")
            result_selector = '#result-textarea:not([disabled])'
            page.wait_for_selector(result_selector, timeout=60000)
            
            # 텍스트 추출
            subtitle_text = page.inner_text('#result-textarea')
            
            browser.close()

            if subtitle_text:
                logger.info("자막 추출 성공!")
                return jsonify({'success': True, 'subtitle': subtitle_text})
            else:
                return jsonify({'success': False, 'error': '자막이 비어있습니다.'}), 500

    except Exception as e:
        logger.error(f"에러 발생: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
