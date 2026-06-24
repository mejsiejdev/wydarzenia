# Wydarzenia

## Uruchomienie projektu

Najpierw należy zainstalować [Python'a](https://www.python.org/downloads/)
oraz [uv](https://docs.astral.sh/uv/getting-started/installation/).

Następnie sprawdzić, czy `uv` jest dostępne:

```bash
$ uv
An extremely fast Python package manager.

Usage: uv [OPTIONS] <COMMAND>

...
```

Po upewnieniu się, że jest dostępne, należy zainstalować wymagane pakiety.

```bash
uv sync
```

Następnie należy ustawić w pliku `.env` zmienną `DATABASE_URL` wskazującą na bazę
danych oraz `JWT_SECRET_KEY` używaną do podpisywania tokenów dostępu (dowolny
długi, losowy ciąg znaków, np. wygenerowany poleceniem `openssl rand -hex 32`).

```bash
DATABASE_URL=postgresql://user:password@localhost:5432/database_name
JWT_SECRET_KEY=<długi losowy ciąg znaków>
```

Przed uruchomieniem należy zastosować migracje bazy danych (zob. [Migracje](#migracje)):

```bash
uv run alembic upgrade head
```

Teraz można uruchomić projekt za pomocą uvicorn:

```bash
uv run uvicorn main:app
```

API jest dostępne pod adresem `http://127.0.0.1:8000`, a interaktywna
dokumentacja pod `http://127.0.0.1:8000/docs`.

## Uwierzytelnianie

Logowanie odbywa się przez `POST /auth/login` (formularz hasłowy OAuth2, pole
`username` przenosi adres e-mail) i zwraca token JWT typu bearer, który następnie
należy przesyłać w nagłówku `Authorization: Bearer <token>`. W interaktywnej
dokumentacji służy do tego przycisk **Authorize**.

Nowe konta otrzymują status `nieaktywowany`: mogą się logować i przeglądać
zawartość, ale nie mogą tworzyć wydarzeń. Tylko moderator może zmienić użytkownikowi
pole `status` lub flagę `blacklisted` (przez `PATCH /users/{id}`). dlatego
pierwszego moderatora trzeba skonfigurować ręcznie:

### Konfiguracja pierwszego moderatora

1. Należy zarejestrować użytkownika przez API albo w interaktywnej dokumentacji
   (`POST /users` pod `http://127.0.0.1:8000/docs`), albo za pomocą curl:

   ```bash
   curl -X POST http://127.0.0.1:8000/users \
     -H "Content-Type: application/json" \
     -d '{"email": "admin@example.com", "password": "password123", "first_name": "Admin", "last_name": "User"}'
   ```

2. Następnie należy nadać temu kontu uprawnienia bezpośrednio w bazie danych,
   używając tego samego connection stringa co `DATABASE_URL` w pliku `.env`:

   ```bash
   psql "postgresql://user:password@localhost:5432/database_name" \
     -c "UPDATE users SET status = 'moderator' WHERE email = 'admin@example.com';"
   ```

3. Należy zalogować się jako użytkownik z nowo dodanymi uprawnieniami. W interaktywnej dokumentacji wystarczy
   kliknąć **Authorize** i podać adres e-mail jako `username` oraz hasło. Jeśli
   użytkownik był już zalogowany przed nadaniem uprawnień, ponowne logowanie nie
   jest konieczne: status jest odczytywany na świeżo z bazy danych przy każdym
   żądaniu.

Moderator może teraz wylistować wszystkich użytkowników (`GET /users`) oraz
zarządzać innymi kontami przez `PATCH /users/{id}`, np. aktywować konto za pomocą
`{"status": "zwykły"}` lub zablokować je za pomocą `{"blacklisted": true}`.

## Testowanie

Zestaw testów to test przepływu end-to-end, który steruje prawdziwym API za pomocą
`fastapi.testclient.TestClient` na rzeczywistej bazie danych Postgres. Wymaga on
**osobnej, pustej** bazy danych, nigdy nie należy kierować go na używane dane.

1. Bazę testową tworzy się raz, np.:

   ```bash
   createdb wydarzenia_test
   ```

2. Należy ustawić `TEST_DATABASE_URL` w pliku `.env` (lub w powłoce) tak, aby
   wskazywała na tę bazę:

   ```bash
   TEST_DATABASE_URL=postgresql://user:password@localhost:5432/wydarzenia_test
   ```

3. Uruchomienie testów:

   ```bash
   uv run pytest -v
   ```

Zestaw testów stosuje migracje alembica na bazie testowej przy starcie, a każdy
test wykonuje się wewnątrz transakcji, która jest następnie wycofywana, dzięki
czemu baza pozostaje pusta. Jeśli `TEST_DATABASE_URL` nie jest ustawiona, testy
są pomijane.

## Migracje

Aby utworzyć migrację, należy uruchomić:

```bash
uv run alembic revision -m "<NAZWA_REWIZJI>"
```

Po dodaniu zawartości migracji należy zastosować wprowadzone w niej zmiany:

```bash
uv run alembic upgrade head
```
