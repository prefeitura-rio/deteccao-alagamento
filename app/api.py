# -*- coding: utf-8 -*-
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests


class APIVisionAI:
    def __init__(self, username, password):
        self.BASE_URL = "https://vision-ai-api-staging-ahcsotxvgq-uc.a.run.app"
        self.username = username
        self.password = password
        self.headers, self.token_renewal_time = self._get_headers()

    def _get_headers(self):
        access_token_response = requests.post(
            f"{self.BASE_URL}/auth/token",
            data={
                "username": self.username,
                "password": self.password,
            },
            timeout=20,  # Add a timeout argument to avoid hanging indefinitely
        ).json()
        token = access_token_response["access_token"]
        return {"Authorization": f"Bearer {token}"}, time.time()

    def _refresh_token_if_needed(self):
        if time.time() - self.token_renewal_time >= 600:
            self.headers, self.token_renewal_time = self._get_headers()

    def _get(self, path):
        self._refresh_token_if_needed()
        try:
            response = requests.get(
                f"{self.BASE_URL}{path}", headers=self.headers, timeout=600
            )
            return response.json()
        except requests.exceptions.ReadTimeout as _:  # noqa
            return {"items": []}

    def _get_all_pages(self, path, page_size=300):
        # Initial request to determine the number of pages
        initial_response = self._get(f"{path}?page=1&size=1")
        if not initial_response:
            return []

        # Assuming the initial response contains the total number of items or pages # noqa
        total_pages = self._calculate_total_pages(initial_response, page_size)

        # Function to get a single page
        def get_page(page):
            # time each execution
            start = time.time()
            print(f"Getting page {page} of {total_pages}")
            response = self._get(f"{path}?page={page}&size={page_size}")
            print(f"Page {page} took {time.time() - start} seconds")
            return response

        data = []
        with ThreadPoolExecutor(max_workers=total_pages) as executor:
            # Create a future for each page
            futures = [
                executor.submit(get_page, page)
                for page in range(1, total_pages + 1)  # noqa
            ]

            for future in as_completed(futures):
                response = future.result()
                if response:
                    data.extend(response["items"])

        return data

    def _calculate_total_pages(self, response, page_size):
        print(response)
        return round(response["total"] / page_size) + 1
