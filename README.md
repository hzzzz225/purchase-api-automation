# 模拟 ERP 采购 API（自动化测试教学环境）

这是一个专门用于学习接口自动化测试的轻量被测服务，不是生产 ERP，也不代表任何企业系统。
它包含真实的业务状态流转和 SQLite 数据持久化，不是固定 JSON 的 Mock。

## 1. 环境要求
- Python 3.10+
- pip

## 2. 安装与启动

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

## 3. 测试账号
| 角色 | 用户名 | 密码 |
|---|---|---|
| 普通测试用户 | tester | Test1234 |
| 管理员演示账号 | admin | Admin1234 |

当前版本使用演示 Token。两个账号用于练习鉴权流程；暂未实现细粒度角色权限控制，不能把它当作真实权限系统。

## 4. 核心业务流程
创建订单（PENDING） -> 审核（APPROVED） -> 入库（RECEIVED）。
订单可在 PENDING 状态修改；PENDING 或 APPROVED 状态可取消。
只有 APPROVED 订单允许入库；重复入库会返回 409，避免库存重复增加。

## 5. 主要接口
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

## 6. 创建订单请求示例

```json
{
  "supplier_id": 1001,
  "items": [
    {"product_id": 2001, "quantity": 10, "unit_price": 25.0},
    {"product_id": 2002, "quantity": 2, "unit_price": 89.0}
  ],
  "remark": "自动化测试采购订单"
}
```

金额由服务端计算：10*25 + 2*89 = 428.00。

## 7. 重要说明
- 这是教学环境，数据保存在本地 SQLite 文件。
- 删除 `purchase_lab.db` 并重新启动服务，可重置全部数据。
- 第一版使用 SQLite 降低环境门槛；后续学习 SQL 校验时再切换 MySQL。
- 当前演示 Token 不含真实密码哈希、刷新机制或细粒度 RBAC。
- 采购入库按订单明细全量入库，暂不支持部分入库。
