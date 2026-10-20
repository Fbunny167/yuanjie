# 本地启动与运行说明

本文适用于从本仓库克隆的源码版。网站在自己的电脑上运行，不需要购买服务器或域名。请在克隆后的仓库目录执行命令，避免启动旧测试包中的网页副本。

## 1. 准备环境与源码

- Windows 10/11，Python 3.11 或更高版本。
- 使用 Git 克隆时需要安装 Git；使用 GitHub Desktop 克隆也可以。
- 首次安装需要联网下载 Python 依赖，后续使用同一个虚拟环境启动。
- 普通运行不需要 Node.js。仓库已包含 `src/yuanjian_agent/ui/` 中的构建后网页资源。

在 PowerShell 中执行：

```powershell
git clone https://github.com/Fbunny167/yuanjie.git
cd yuanjie
py -3 --version
```

最后一条命令应显示 Python 3.11 或更新版本。如果无法识别 `py`，可检查 `python --version`；若两者都不可用，请先安装 Python，再重新打开终端。

## 2. 安装依赖

在仓库根目录双击 `首次安装.cmd`，或执行：

```powershell
.\首次安装.cmd
```

脚本会检查 Python 版本、创建 `.venv/`，安装项目及开发依赖，并执行 `pip check`。看到 `Installation complete` 后再启动网站；安装报错时先处理错误，不要反复启动。

如果电脑安装了多个 Python，可指定已安装解释器的实际路径：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup_teammate.ps1 -PythonExe 'C:\实际的Python目录\python.exe'
```

也可以手动安装；以下命令使用已安装的 Python 3.11：

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pip check
```

请使用虚拟环境中的 `python.exe` 安装和运行，避免依赖装到另一个 Python 环境。

## 3. 启动并访问网页

双击 `启动网站.cmd`，或在仓库根目录执行：

```powershell
.\启动网站.cmd
```

等待后台服务启动后，在浏览器打开：

<http://127.0.0.1:8002/app/>

启动脚本会启动隐藏的后台进程，并将日志和本机数据写到 `.local-phase2/`。因此，关闭启动脚本窗口不一定会停止网站。`127.0.0.1` 指当前电脑，队友应在自己的电脑上克隆并启动。

需要在终端直接观察启动错误时，可改为前台运行：

```powershell
.\.venv\Scripts\python.exe .\scripts\run_web.py --port 8002 --data-dir .\.local-phase2
```

前台运行时保留该终端，按 `Ctrl+C` 停止。上述命令是故障排查用的基础运行方式；如需使用已配置的本地模型，请优先使用启动脚本，保持模型验证流程一致。

## 4. 页面无法访问时如何排查

### 浏览器提示“拒绝连接”

先确认当前仓库已成功安装依赖、启动脚本没有报错，且地址是 `http://127.0.0.1:8002/app/`，没有使用旧端口或 `https`。

查看服务端口是否正在监听：

```powershell
Get-NetTCPConnection -LocalPort 8002 -State Listen -ErrorAction SilentlyContinue |
    Select-Object LocalAddress, LocalPort, OwningProcess
```

没有输出通常表示服务尚未启动或已退出。检查本次启动的日志：

```powershell
Get-Content .\.local-phase2\server.err.log -Tail 60
Get-Content .\.local-phase2\server.out.log -Tail 60
```

若日志文件尚不存在，说明启动可能在创建服务前就失败，应查看启动窗口中的错误。出现缺少模块、找不到虚拟环境等提示时，回到第 2 节检查安装结果。

### 提示端口已占用，或打开了其他页面

启动脚本检测到端口占用会提示后退出，不会自动确认该端口运行的是否就是源界。先核对端口所属进程，或直接选用空闲端口，例如：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start_teammate.ps1 -Port 8012
```

随后访问 <http://127.0.0.1:8012/app/>，不要继续刷新旧端口。

### 地址能连接，但页面空白或返回 404

- 确认地址包含 `/app/`，先尝试 `Ctrl+F5` 强制刷新。
- 确认克隆完整，`src/yuanjian_agent/ui/index.html` 和 `assets/` 均存在。
- 若修改过前端，请按第 5 节重新构建。检查浏览器开发者工具的 Console、Network 和后台日志，区分静态资源加载失败与接口报错。

### 安装依赖失败，或提示模型校验失败

- 依赖下载失败时，检查网络、代理或 Python 包源，修复后重新执行安装步骤。
- 模型是可选组件。仓库默认不携带模型权重；没有本地模型时，网页能否打开与模型是否参与分析是两个问题，扫描效果应以页面实际覆盖状态为准。
- 如另行配置了 `models/paraphrase-multilingual-MiniLM-L12-v2/`，启动脚本还会检查模型依赖与权重。若提示缺少 `experiments/fetch_contract_model.py` 或模型校验失败，请联系维护者核对配套文件和模型版本，不要仅凭网页可访问就认为模型已正常工作。

反馈问题时，提供 Python 版本、使用的启动命令、访问地址及相关报错即可。分享日志或截图前去掉真实密钥、个人信息和扫描数据。

## 5. 修改前端后的构建

仅运行网站可以跳过本节。修改 `frontend/` 源码后，需要重新构建才能让后端提供新页面。准备兼容 Vite 7 的 Node.js，例如 Node.js 22.12 或更新的 22.x 版本，并安装其附带的 npm。

在仓库根目录执行：

```powershell
cd frontend
npm ci
npm run build
cd ..
```

构建输出到 `src/yuanjian_agent/ui/`，然后强制刷新网页。若使用 `npm run dev`，开发服务器通常位于 `http://127.0.0.1:5173/app/`，仍需另行启动后端；其默认 API 代理指向 `http://127.0.0.1:8002`。更改后端端口后，需要相应设置 `OPENGUARD_API_TARGET` 再启动开发服务器。

## 6. 确认启动成功

1. 能打开欢迎页并进入对应的审查入口。
2. 使用 `examples/` 中的合成案例检查上传、结果和证据展示。
3. 需要报告时，再验证相应的导出功能。

页面成功打开只证明服务可访问，实际检测模块、模型和报告功能应分别验证。`.venv/`、`.cache/` 和 `.local-phase2/` 是本机环境或运行数据，不要提交到仓库。
