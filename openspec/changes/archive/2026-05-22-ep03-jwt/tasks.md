## 1. Config & dependencies

- [x] 1.1 Add JWT/bcrypt settings to `config.py`, `.env.example`, `requirements.txt`
  - 预计文件：3 · 层：core/config

- [x] 1.2 Add `core/security.py` (hash, create/verify token) + `core/deps.py` (`get_current_user`)
  - 预计文件：2 · 层：core

## 2. Auth API (backend)

- [x] 2.1 Harness `test_auth_contract.py` — register/login/me 契约（TDD 先写）
  - 预计文件：1 · Harness L1

- [x] 2.2 `AuthService` + `POST /auth/register`, `POST /auth/login`
  - 预计文件：3 · 层：services + schemas + api/v1/auth

- [x] 2.3 `GET /me` + router 注册
  - 预计文件：2 · 层：api/v1 + router.py

## 3. Frontend (Story 3.4)

- [x] 3.1 `apps/web` 登录页 `/login` + 表单
  - 预计文件：2 · 层：app/login、components

- [x] 3.2 API client Token 拦截器 + 401 跳转
  - 预计文件：2 · 层：lib/

- [x] 3.3 注册页 `/register` + 注册后自动登录
  - 预计文件：2 · 层：app/register、components

## 4. Docs & epic

- [x] 4.1 更新 BE-engineering、`docs/database.md` 鉴权说明；勾选 EP03 Story 3.4
  - 预计文件：2 · docs
