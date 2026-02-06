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

        with sync_playwright() as p:
            # 브라우저 실행 (메모리 최적화 옵션)
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-gpu'
                ]
            )
            # 모바일처럼 속여서 접속 (가끔 더 빠름)
            context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
            page = context.new_page()

            # ★핵심 수정: 로봇의 인내심을 90초로 설정 (기본 30초는 너무 짧음)
            page.set_default_timeout(90000)

            # 사이트 접속
            logger.info("사이트 접속 중...")
            page.goto('https://subtitle-c2419.firebaseapp.com/ko/')
            
            # ★핵심 수정: networkidle 제거 (속도 향상)
            # 그냥 입력창이 보이면 바로 입력 시작하도록 변경

            # 언어 선택
            page.select_option('#languages', language)
            
            # URL 입력
            page.fill('#url-input', video_url)
            
            # Paste 버튼이 있으면 클릭 (없으면 무시)
            if page.is_visible('button:has-text("Paste")'):
                page.click('button:has-text("Paste")')

            # 변환(Submit) 버튼 활성화 대기
            submit_selector = 'button.button:not([disabled])'
            page.wait_for_selector(submit_selector)
            
            # 버튼 클릭
            logger.info("변환 버튼 클릭")
            page.click(submit_selector)

            # 결과 대기
            logger.info("결과 기다리는 중...")
            result_selector = '#result-textarea:not([disabled])'
            page.wait_for_selector(result_selector)
            
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
