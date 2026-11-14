# 模拟 ERP 采购 API
## 1. 项目介绍

基于模拟采购业务系统构建的自动化测试项目，
覆盖采购订单创建、审核、入库、取消等业务流程。

## 2. 技术栈

- Python
- Pytest
- Requests
- Selenium
- PyMySQL
- MySQL
- Allure
- pytest-html

## 3. 测试范围

- API 接口测试
- UI 自动化测试
- 数据库一致性校验
- 正常场景与异常场景
- 边界值测试
- 采购订单状态流转
- 库存及库存流水验证
## 4. 环境要求
- Python 3.10+
- pip

## 5. 安装与启动

在项目根目录打开终端：

```bash
python -m venv .venv
```

Windows PowerShell：
```powershell
.venv\Scripts\Activate.ps1
```

macOS / Linux：
```bash
source .venv/bin/activate
```

安装依赖并启动：
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

访问：
- 健康检查：http://127.0.0.1:8000/health
- Swagger 接口文档：http://127.0.0.1:8000/docs

首次启动会自动创建 SQLite 数据库 `purchase_lab.db` 和基础测试数据。

## 6. 测试账号
| 角色 | 用户名 | 密码 |
|---|---|---|
| 普通测试用户 | tester | Test1234 |

## 7. 主要接口
| 方法 | 路径 | 用途 |
|---|---|---|
| POST | `/api/auth/login` | 获取 Token |
| GET | `/api/suppliers` | 供应商列表 |
| GET | `/api/products` | 商品列表 |
| POST | `/api/purchase-orders` | 创建采购订单 |
| GET | `/api/purchase-orders` | 订单列表，支持 status/page/page_size |
| GET | `/api/purchase-orders/{id}` | 订单详情 |
| PUT | `/api/purchase-orders/{id}` | 修改待审核订单 |
| POST | `/api/purchase-orders/{id}/approve` | 审核订单 |
| POST | `/api/purchase-orders/{id}/receive` | 采购入库 |
| POST | `/api/purchase-orders/{id}/cancel` | 取消订单 |
| GET | `/api/stock-movements` | 库存变动记录 |

除 `/health` 和登录接口外，其余接口均需请求头：
`Authorization: Bearer training-token`

## 8. 项目特点

- Pytest Fixture 管理测试资源
- Page Object 模式封装 UI 页面
- API 客户端统一封装
- UUID 测试数据隔离
- 自动清理测试数据
- MySQL 数据一致性校验
- Allure 自动化测试报告

## 9. 执行测试

运行 API 测试：

    pytest -v -s tests -m api

运行 UI 测试：

    pytest -v -s tests -m ui

运行全部测试：

    pytest -v -s tests

测试报告

Allure：

    allure serve reports/allure-results
