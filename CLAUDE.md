# 股票分析软件 - AI 助手指引

## 项目简介
这是一款 Windows 桌面股票分析软件，面向**非技术用户**。使用 Python + CustomTkinter 构建，提供 A 股收益率查询、回本计算、记录管理功能。最终打包为单个 `.exe` 文件分发。

## 标准文件指引

| 文件 | 路径 | 用途 |
|------|------|------|
| 需求规格 | [docs/01-需求规格.md](docs/01-需求规格.md) | 完整功能需求与边界情况 |
| 技术选型 | [docs/02-技术选型.md](docs/02-技术选型.md) | 技术栈说明与选型理由 |
| 设计规范 | [docs/03-设计规范.md](docs/03-设计规范.md) | UI 配色、字体、布局、组件规范 |
| 实施步骤 | [docs/04-实施步骤.md](docs/04-实施步骤.md) | 分步执行清单（含勾选框） |
| 开发计划 | 用户的 Claude 计划文件 | 最终确认的技术方案 |

## 工作约定

### 开发方式
1. **小步推进**：每次只完成一个步骤，验证通过后再进入下一步
2. **先读规范**：每次开发前，先查阅 `docs/` 下的相关规范文件
3. **中文优先**：代码中的注释、UI 文字、文档均使用中文
4. **用户友好**：所有错误提示使用通俗易懂的中文，避免技术术语

### 代码规范
- 使用有意义的变量和函数名（中文拼音可接受，英文更佳）
- 每个 `.py` 文件顶部添加一行注释说明文件用途
- 异常处理必须有用户友好的中文提示
- UI 组件尺寸、颜色严格遵循 [docs/03-设计规范.md](docs/03-设计规范.md)

### 运行与测试
```bash
# 激活虚拟环境
venv\Scripts\activate

# 运行程序
python main.py

# 单独测试某个模块
python -m data.fetcher
```

### 打包
```bash
# 使用 build.bat 一键打包
build.bat
```

## 目录结构
```
d:\个人\分析软件\
├── CLAUDE.md            # ← 本文件
├── docs/                # 开发文档（需求、技术、设计、步骤）
├── main.py              # 程序入口
├── app.py               # 主窗口 + 导航
├── ui/                  # UI 页面
│   ├── page_return.py   # 功能一：收益率查询
│   ├── page_recovery.py # 功能二：回本计算
│   ├── page_records.py  # 功能三：我的记录
│   └── components.py    # 可复用组件
├── data/
│   ├── fetcher.py       # 数据获取（akshare）
│   └── storage.py       # 本地存储（SQLite）
├── utils/
│   └── calculator.py    # 计算逻辑
├── assets/              # 图标等静态资源
├── requirements.txt     # Python 依赖
└── build.bat            # 打包脚本
```

## 注意事项
- 用户是编程小白，软件操作流程必须简洁明了
- akshare 是免费数据源，请求频率不宜过高
- SQLite 数据库文件 `records.db` 自动创建在 `data/` 目录下
- 打包后的 exe 需要包含 matplotlib 和 akshare 的依赖数据
- CustomTkinter 的日期选择器需自建（框架无内置 date picker）
