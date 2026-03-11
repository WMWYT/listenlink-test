from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import requests
import json
import time

app = Flask(__name__)
CORS(app)

# 缓存音频URL，避免重复请求
audio_cache = {}
CACHE_DURATION = 300  # 5分钟缓存

@app.route('/api/video/<bvid>', methods=['GET'])
def get_video_info(bvid):
    """
    获取视频信息和音频URL
    """
    try:
        # 检查缓存
        cache_key = f"video_{bvid}"
        if cache_key in audio_cache:
            cached_data = audio_cache[cache_key]
            if time.time() - cached_data['timestamp'] < CACHE_DURATION:
                return jsonify({
                    'code': 0,
                    'message': 'success (cached)',
                    'data': cached_data['data']
                })

        # 步骤1：获取视频基本信息
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://www.bilibili.com/',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Origin': 'https://www.bilibili.com'
        }

        url = f'https://api.bilibili.com/x/web-interface/view?bvid={bvid}'
        response = requests.get(url, headers=headers, timeout=30)
        data = response.json()

        if data.get('code') != 0 or not data.get('data'):
            return jsonify({
                'code': data.get('code', -1),
                'message': data.get('message', '获取视频信息失败')
            }), 400

        video_data = data['data']
        cid = video_data.get('cid')

        if not cid:
            return jsonify({
                'code': -1,
                'message': '无法获取视频 CID'
            }), 400

        # 步骤2：获取播放地址
        playurl_url = f'https://api.bilibili.com/x/player/playurl?bvid={bvid}&cid={cid}&qn=16&fnver=0&fnval=16&otype=json'
        playurl_response = requests.get(playurl_url, headers=headers, timeout=30)
        playurl_data = playurl_response.json()

        if playurl_data.get('code') == 0 and playurl_data.get('data'):
            play_data = playurl_data['data']

            if 'dash' in play_data and 'audio' in play_data['dash']:
                audio_list = play_data['dash']['audio']

                if audio_list:
                    audio_info = audio_list[0]

                    result_data = {
                        'bvid': bvid,
                        'title': video_data.get('title', ''),
                        'pic': video_data.get('pic', ''),
                        'duration': video_data.get('duration', 0),
                        'audio_url': audio_info.get('base_url', ''),
                        'audio_id': audio_info.get('id', ''),
                        'bandwidth': audio_info.get('bandwidth', 0),
                        'mime_type': audio_info.get('mime_type', 'audio/mp4'),
                        'proxy_required': True  # 需要代理播放
                    }

                    # 缓存结果
                    audio_cache[cache_key] = {
                        'timestamp': time.time(),
                        'data': result_data
                    }

                    return jsonify({
                        'code': 0,
                        'message': 'success',
                        'data': result_data
                    })

        return jsonify({
            'code': -1,
            'message': '该视频可能需要登录或会员权限才能播放'
        }), 400

    except Exception as e:
        return jsonify({
            'code': -1,
            'message': f'服务器内部错误: {str(e)}'
        }), 500

@app.route('/proxy/audio', methods=['GET'])
def proxy_audio():
    """
    智能音频代理：添加必要请求头转发音频请求
    """
    try:
        audio_url = request.args.get('url')
        if not audio_url:
            return jsonify({'error': '缺少 url 参数'}), 400

        # Bilibili 音频服务器需要的请求头
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://www.bilibili.com/',
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'identity',  # 重要：不压缩，直接传输
            'Range': request.headers.get('Range', ''),  # 支持断点续传
            'Origin': 'https://www.bilibili.com'
        }

        print(f"代理音频请求: {audio_url[:50]}...")

        # 发起请求到 Bilibili 音频服务器
        response = requests.get(audio_url, headers=headers, timeout=60, stream=True)

        if response.status_code == 200 or response.status_code == 206:
            # 流式返回音频数据
            def generate():
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        yield chunk

            # 设置正确的响应头
            resp_headers = {
                'Content-Type': 'audio/mp4',
                'Accept-Ranges': 'bytes',
                'Cache-Control': 'public, max-age=3600'
            }

            # 如果有 Content-Length，传递它
            if 'content-length' in response.headers:
                resp_headers['Content-Length'] = response.headers['content-length']

            return Response(
                generate(),
                status=response.status_code,
                headers=resp_headers,
                mimetype='audio/mp4'
            )
        else:
            print(f"音频服务器返回错误: {response.status_code}")
            return jsonify({'error': f'获取音频失败: {response.status_code}'}), response.status_code

    except requests.exceptions.Timeout:
        print("音频请求超时")
        return jsonify({'error': '音频请求超时'}), 504
    except Exception as e:
        print(f"代理音频错误: {str(e)}")
        return jsonify({'error': f'代理请求失败: {str(e)}'}), 500

@app.route('/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({
        'status': 'ok',
        'cached_items': len(audio_cache),
        'uptime': time.time()
    })

if __name__ == '__main__':
    print('混合版代理服务器启动在 http://127.0.0.1:5000')
    print('此版本智能代理音频流量，添加必要请求头')
    print('请确保已安装依赖: pip install flask flask-cors requests')
    app.run(debug=True, host='127.0.0.1', port=5000)
