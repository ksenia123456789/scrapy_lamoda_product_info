import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup
import time, json, random, os, pickle, requests
from selenium.common.exceptions import TimeoutException, WebDriverException
import re


def human_sleep(a=1.0, b=2.5):
    time.sleep(random.uniform(a, b))


def save_cookies(driver, path="cookies.pkl"):
    try:
        with open(path, "wb") as f:
            pickle.dump(driver.get_cookies(), f)
        print(f"Cookies сохранены в {path}")
    except Exception as e:
        print(f"Ошибка при сохранении cookies: {e}")


def load_cookies(driver, path="cookies.pkl"):
    if os.path.exists(path) and os.path.getsize(path) > 0:
        try:
            with open(path, "rb") as f:
                cookies = pickle.load(f)
                for cookie in cookies:
                    try:
                        driver.add_cookie(cookie)
                    except:
                        pass
            print(f"Cookies загружены из {path}")
        except Exception as e:
            print(f"Ошибка при загрузке cookies: {e}")
            os.remove(path) if os.path.exists(path) else None
    else:
        print(f"Файл {path} не существует или пустой")


options = uc.ChromeOptions()
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36")
driver = uc.Chrome(version_main=141, options=options, headless=False)

try:
    url = "https://www.lamoda.ru/c/355/clothes-zhenskaya-odezhda/"
    print(f"Загружаем: {url}")
    driver.get(url)

    load_cookies(driver)
    driver.refresh()
    human_sleep(10, 12)

    driver.execute_script("window.focus();")
    print("Окно браузера активировано")

    try:
        driver.execute_script(
            "document.querySelectorAll('div[class*=\"modal\"], div[class*=\"popup\"]').forEach(el => el.style.display = 'none');")
        print("Всплывающие окна скрыты")
    except:
        print("Всплывающие окна не найдены")

    try:
        auth_popup = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[class*='modal-auth'], div[class*='phone']"))
        )
        popup_text = auth_popup.text
        if "Введите телефон" in popup_text or "код подтверждения" in popup_text:
            print("Обнаружено окно авторизации! Нажми Enter после ввода телефона и кода...")
            input()
            save_cookies(driver)
        else:
            print(f"Обнаружено модальное окно, но не авторизация: {popup_text[:100]}...")
            try:
                close_button = auth_popup.find_element(By.CSS_SELECTOR,
                                                       "button[class*='close'], a[class*='close'], [data-testid='modal-close']")
                close_button.click()
                print("Модальное окно закрыто")
            except:
                print("Не удалось закрыть модальное окно")
    except:
        print("Капча/авторизация не обнаружена")

    current_url = driver.current_url
    if current_url != url:
        print(f"Редирект на: {current_url}")
    else:
        print("Нет редиректа")

    WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1")))
    print("Заголовок найден")

    print("Собираем ссылки на товары...")
    product_links = []
    last_card_count = 0
    max_iterations = 1000
    iteration = 0
    page = 1
    TARGET = 5500

    while iteration < max_iterations and len(product_links) < TARGET:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        human_sleep(10, 12)

        # Имитация активности окна
        driver.execute_script("window.focus();")
        try:
            action = ActionChains(driver)
            action.move_by_offset(random.randint(50, 200), random.randint(50, 200)).perform()
        except:
            pass

        # Собираем ссылки
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.x-product-card__card"))
            )
            cards = driver.find_elements(By.CSS_SELECTOR, "div.x-product-card__card")
            new_links = []
            for card in cards:
                try:
                    link_element = card.find_element(By.CSS_SELECTOR,
                                                     "div.x-product-card__link.x-product-card__hit-area > a")
                    link = link_element.get_attribute("href")
                    if link and not link.startswith("https://www.lamoda.ru"):
                        link = "https://www.lamoda.ru" + link
                    if link not in product_links and link not in new_links:
                        new_links.append(link)
                        if len(product_links) + len(new_links) >= TARGET:
                            break
                except:
                    continue
            product_links.extend(new_links)
            card_count = len(product_links)
            print(f"Итерация {iteration + 1}: {card_count} ссылок (цель: {TARGET})")

            # ОСТАНОВКА НА 5500
            if len(product_links) >= TARGET:
                product_links = product_links[:TARGET]
                print(f"ЦЕЛЬ ДОСТИГНУТА: собрано {TARGET} ссылок. Останавливаем сбор.")
                break

        except:
            print(f"Ошибка при сборе ссылок на итерации {iteration + 1}")
            break

        # Проверяем кнопку "Показать ещё"
        try:
            show_more_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR,
                                            "button[class*='show-more'], a[class*='show-more'], button[data-testid='showMoreButton'], "
                                            "button[class*='load-more'], button[class*='showMore'], a[class*='loadMore'], "
                                            "button[class*='showMoreButton'], button[class*='button-more'], button[data-action*='load']"))
            )
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                                  show_more_button)
            human_sleep(1, 2)
            show_more_button.click()
            print(f"Нажата кнопка 'Показать ещё' на итерации {iteration + 1}")
            human_sleep(10, 12)
        except:
            print(f"Кнопка 'Показать ещё' не найдена на итерации {iteration + 1}")

        # Проверка на отсутствие новых ссылок
        if card_count == last_card_count and iteration > 5:
            print(f"Новых ссылок не найдено на итерации {iteration + 1}")
            try:
                next_page = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR,
                                                "a.pagination__next, a[class*='next-page'], a[class*='pagination'][href*='page'], a.next"))
                )
                next_url = next_page.get_attribute("href")
                print(f"Переход на следующую страницу: {next_url}")
                driver.get(next_url)
                human_sleep(10, 12)
                save_cookies(driver)
                last_card_count = 0
                iteration = 0
                page += 1
                continue
            except:
                print(f"Пагинация завершена на странице {page}")
                break
        last_card_count = card_count
        iteration += 1

    print(f"Сбор ссылок завершён, найдено {len(product_links)} ссылок")
    with open("product_links.json", "w", encoding="utf-8") as f:
        json.dump(product_links, f, ensure_ascii=False, indent=2)
    print("Сохранены ссылки в product_links.json")

    # === УДАЛЕНО: debug HTML ===
    # with open("lamoda_page_source_debug.html", ...) — УДАЛЕНО

    results = []
    for i, link in enumerate(product_links, 1):
        retries = 2
        for attempt in range(retries):
            try:
                print(f"Переходим на: {link}")
                driver.get(link)
                human_sleep(15, 20)

                driver.execute_script("window.focus();")

                try:
                    WebDriverWait(driver, 40).until(
                        lambda d: d.execute_script("return typeof window.__NUXT__ !== 'undefined'")
                    )
                except:
                    print(f"Карточка {i}: Не загрузилась страница товара или __NUXT__ не найден")
                    break

                soup = BeautifulSoup(driver.page_source, 'html.parser')

                # === УДАЛЕНЫ ВСЕ DEBUG-ФАЙЛЫ ===
                # product_{id}_debug.html — УДАЛЕНО
                # script_debug_*.txt — УДАЛЕНО
                # nuxt_debug_*.json — УДАЛЕНО
                # api_debug_*.json — УДАЛЕНО

                brand, title, price, description, material, color, sizes = "", "", "", "", "", "", []
                images = []
                rating = ""
                reviews_count = ""
                season = ""
                country = ""
                attributes = []
                colored_products = []

                try:
                    nuxt_data = driver.execute_script("return window.__NUXT__;")
                    if nuxt_data:
                        product_data = None
                        possible_paths = [
                            lambda x: x.get('payload', {}).get('state', {}).get('payload', {}).get('product', {}),
                            lambda x: x.get('data', [{}])[0].get('payload', {}).get('product', {}),
                            lambda x: x.get('payload', {}).get('product', {}),
                            lambda x: x.get('state', {}).get('data', {}).get('payload', {}).get('product', {}),
                            lambda x: x.get('state', {}).get('product', {}),
                            lambda x: x.get('state', {}).get('catalog', {}).get('product', {}),
                            lambda x: x.get('payload', {}) if 'brand' in x.get('payload', {}) else {}
                        ]
                        for path in possible_paths:
                            try:
                                candidate = path(nuxt_data)
                                if candidate and ('brand' in candidate or 'title' in candidate):
                                    product_data = candidate
                                    break
                            except:
                                continue

                        if product_data:
                            brand = product_data.get('brand', {}).get('title', '') or product_data.get('brand_name', '')
                            title = product_data.get('title', '') or product_data.get('name', '')
                            price = str(product_data.get('prices', {}).get('onsite', {}).get('price', '') or product_data.get('price', '') or product_data.get('current_price', ''))
                            description = product_data.get('brand', {}).get('description', '') or product_data.get('seo_title', '') or product_data.get('description', '')
                            attributes = product_data.get('attributes', [])
                            for attr in attributes:
                                key = attr.get('key', '').lower()
                                if key in ['material_filling', 'material', 'состав', 'materials']:
                                    material = attr.get('value', '')
                                if key in ['color_family', 'color', 'цвет']:
                                    color = attr.get('value', '')
                            sizes = [size.get('title', '') or size.get('brand_title', '') for size in product_data.get('sizes', []) if size.get('title') or size.get('brand_title')]
                            images = product_data.get('gallery', []) or product_data.get('images', [])
                            rating = product_data.get('average_rating', '')
                            reviews_count = product_data.get('counters', {}).get('reviews', '') or product_data.get('reviews', {}).get('count', '')
                            season = [s.get('title', '') for s in product_data.get('seasons', [])]
                            country = next((a.get('value', '') for a in attributes if a.get('key', '').lower() == 'production_country'), '')
                            colored_products = product_data.get('colored_products', [])

                except Exception as e:
                    print(f"Карточка {i}: Ошибка извлечения __NUXT__: {e}")

                result = {
                    "brand": brand,
                    "title": title,
                    "price": price,
                    "link": link,
                    "category": "Женская одежда",
                    "description": description,
                    "material": material,
                    "color": color,
                    "sizes": sizes,
                    "images": images,
                    "rating": rating,
                    "reviews_count": reviews_count,
                    "season": season,
                    "country": country,
                    "attributes": attributes,
                    "colored_products": colored_products,
                }
                results.append(result)
                print(f"{i}. {brand} | {title} | {price} | {link}")

                save_cookies(driver)
                break

            except Exception as e:
                print(f"Ошибка карточки {i} (попытка {attempt + 1}/{retries}): {e}")
                if attempt < retries - 1:
                    human_sleep(5, 7)
                    driver.refresh()
                    continue
                break

    # Сохраняем результаты
    filename = "lamoda_womens_850_комп.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\nУСПЕХ! Сохранено {len(results)} товаров в {filename}")

finally:
    print("Закрываем браузер...")
    try:
        driver.quit()
    except Exception as e:
        print(f"Ошибка при закрытии браузера: {e}")