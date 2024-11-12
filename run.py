import multiprocessing
from api import flask_app
import asyncio
from main_test_v7_api1 import main_async

def run_flask():
    flask_app.run(host='0.0.0.0', port=5000, threaded=True)

def run_async_main():
    asyncio.run(main_async())

if __name__ == '__main__':
    # Create processes for Flask and async main
    flask_process = multiprocessing.Process(target=run_flask)
    async_process = multiprocessing.Process(target=run_async_main)

    # Start both processes
    flask_process.start()
    async_process.start()

    try:
        # Wait for processes to complete
        flask_process.join()
        async_process.join()
    except KeyboardInterrupt:
        # Handle graceful shutdown
        flask_process.terminate()
        async_process.terminate()
        flask_process.join()
        async_process.join() 