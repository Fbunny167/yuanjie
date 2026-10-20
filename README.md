# 源界

源界是一套面向 Python Agent 项目与静态 MCP 配置的发布前安全审查工具。它以本地静态分析为主，检查敏感凭据、许可证/依赖信息、Agent—Tool 绑定关系以及工具能力暴露风险，并提供 Web 工作台、CLI/API、持久化结果和 HTML/PDF 报告。

## 参赛提交版包含什么

- 可运行的 Python/FastAPI 后端和 Vue Web 工作台
- Secret、License、Agent/Tool/MCP 静态分析模块
- 可定位、脱敏的 Finding 与 Evidence
- `examples/` 中的安全合成示例
- `tests/` 与 `integration_tests/` 中的回归和安全测试
- Windows 安装/启动脚本、许可证和第三方资源清单

本仓库是本地运行版，不是公网演示站。评审者下载后在自己的电脑上启动即可。

## Windows 快速开始

环境要求：Python 3.11 或更高版本，Windows 10/11，首次安装需要网络获取 Python 依赖。

1. 双击 `首次安装.cmd`，等待依赖安装完成。
2. 双击 `启动网站.cmd`。
3. 浏览器打开 <http://127.0.0.1:8002/app/>。

也可以在项目根目录执行：

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\启动网站.cmd
```

首次安装脚本会在本机创建 `.venv/`；该目录不属于开源提交内容。

完整的环境检查、手动启动、端口调整和页面无法访问的排查步骤，见 [本地启动与运行说明](docs/LOCAL_RUNNING.md)。仓库已包含构建后的网页资源，只运行网站时无需安装 Node.js。

## 使用流程

1. 在欢迎页选择检查场景。
2. 上传待审项目目录或 ZIP。
3. 等待静态分析完成。
4. 查看风险、证据、模块覆盖状态和不确定性说明。
5. 在报告页导出 JSON/HTML/PDF 结果。

源界不会导入、安装或执行待审项目代码，不会启动待审 MCP Server，也不会验证真实凭据。ZIP 导入会先检查路径穿越、符号链接、文件数量、体积和压缩比。

## 项目结构

```text
src/yuanjian_agent/   后端、扫描引擎、规则、模板和构建后的 Web 资源
frontend/              Vue 前端源码
examples/              可复现的合成示例
tests/                 单元、API 和安全回归测试
integration_tests/     集成测试
scripts/               安装、启动和 Web 服务脚本
docs/                  面向评审的技术概览
```

## 验证

在已安装开发依赖的环境执行：

```powershell
pytest
```

测试结果只能证明当前代码和测试样例的覆盖范围，不能替代对真实项目的人工复核，也不构成法律合规意见。

## AI、开源与第三方边界

技术报告中披露了 AI 的实际参与、自主开发部分、AI 辅助开发过程和人工验证边界。仓库中的许可证、第三方资源清单、规则和示例均应结合人工审查使用。

- 项目许可证：见 `LICENSE`
- 第三方资源、版本、来源和许可证：见 `THIRD_PARTY_RESOURCES.md`
- 安全边界：见 `SECURITY.md`

当前版本用于竞赛演示和本地验证，不宣称 Production Ready。
