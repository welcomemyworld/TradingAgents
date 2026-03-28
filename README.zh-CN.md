# Future Invest

[English](README.md) | 简体中文

Future Invest 不是一个 AI 荐股器。

它更像一个面向投资流程的 AI 工作系统，目标不是“帮你写一份研究报告”，而是把研究真正变成一个可以讨论、可以执行、可以复盘的投资决策包。

它不会停在“写完一份 memo”这一步，而是运行一条更精简的机构决策闭环：
先做研究，再做反驳，再综合判断，最后落到仓位构建。

你最终拿到的是：
- 一个面向组合语境的判断，而不是泛泛的市场观点
- 一份可讨论、可执行的“决策包”，而不只是研究摘要
- 明确的失效条件，也就是“什么情况下这个想法应该被砍掉”
- 明确的后续跟踪指标，也就是“买了之后要盯什么”
- 默认更短、更直接的 `lean` 模式；需要时再进入更完整的机构评审路径

<div align="center">

不是 stock picker。不是 memo generator。  
而是一条面向组合决策的精简机构闭环。

</div>

Future Invest 最适合被理解成这样一条机构流程：

`mandate and context -> parallel research -> thesis vs challenge -> position packet -> memory and evaluation`

如果用更白话的话说，它做的事其实是：

1. 先定义这到底是不是一个值得研究的仓位问题
2. 用几条不同角度的研究路径并行看它
3. 让系统自己正反辩论，而不是一味强化单边观点
4. 产出一份真正能拿去讨论仓位的结果
5. 把这次运行留下来，供以后复盘和继续学习

在 `lean` 模式下，系统会在“这份决策包已经可以拿去讨论”时停下。  
在 `full` 模式下，同一份决策包还可以继续进入更深的执行、风控和 committee review。

## 一句话理解

如果你第一次接触这个项目，可以先把它理解成：

**一个把“研究结论”进一步加工成“仓位决策”的 AI 系统。**

很多金融 AI 工具做到的是：

`帮你分析一个股票`

Future Invest 想做到的是：

`帮你形成一个可以被投资团队讨论的仓位方案`

两者的差别在于，后者不仅要回答“这家公司怎么看”，还要回答：

- 要不要做
- 为什么是现在做
- 做多大
- 什么情况下这个判断失效
- 建仓之后该盯什么

## 为什么值得关注

大多数金融 AI 工具最后停在“分析”。

Future Invest 试图把终点往前推一步：

`mandate -> research -> thesis vs challenge -> position packet`

这里真正的产品不是一篇研究报告，而是一个可用于机构讨论的决策包。  
它不是输出“这是我的 memo”，而是尽量输出：

- `stance`
- `size`
- `entry framework`
- `kill criteria`
- `monitoring triggers`

这个仓库更适合这样的 AI builder：  
你想做的不是一个金融聊天机器人，也不是一个单纯的研究 copilot，而是一个更接近真实投资流程的工作流系统。

### 为什么它容易被记住

- 它围绕的是机构决策闭环，而不是通用问答流程。
- 它把输出压缩成 position-construction packet，而不是长篇 narrative memo。
- 它在形成强观点之前，就把 portfolio context 放到前面。
- 它保留了 institutional memory，让多次运行可以积累而不是反复从零开始。
- 它内置 evaluation harness，可以测试流程质量，而不是只靠主观感觉。

### 它和常见研究 Agent 的区别

| 维度 | 常见研究 Agent | Future Invest |
| --- | --- | --- |
| 工作单元 | 回答或 memo | 机构决策闭环 |
| 最终产物 | 研究叙述 | Position packet |
| 推理结构 | 单轮 assistant | Debate + synthesis |
| 组合语境 | 往往较晚出现或默认省略 | 在 thesis 形成前引入 |
| Memory | 大多近似无状态 | 跨运行的 institutional memory |

> Future Invest 适合做研究工作流和机构决策流程原型。它不是金融、投资或交易建议。

## 你会得到什么

一次成功的运行，理想状态不应该只是“分析完成”，而应该更像“已经能拿去开会讨论这个仓位了”。

一个典型决策包会长这样：

```yaml
stance: long
variant: market underestimates earnings durability
portfolio_role: core growth seat
size: medium
entry_framework: build on weakness around catalyst window
kill_criteria:
  - thesis breaks if demand normalization stalls for two quarters
  - cut if catalyst path slips and expectations reset higher anyway
monitoring:
  - estimate revisions
  - positioning and crowding
  - next catalyst date
missing_evidence:
  - channel check quality
  - management credibility under new guidance
```

如果把上面这份输出翻成人话，大概就是：

- `stance`：到底看多、看空，还是先不做
- `variant`：你和市场最核心的不一样看法是什么
- `portfolio_role`：这个仓位在组合里扮演什么角色
- `size`：仓位是大、是小，还是先试仓
- `entry_framework`：更适合什么时候进、怎么进
- `kill_criteria`：什么情况出现就说明 thesis 失效了
- `monitoring`：进场之后最该持续盯的几个指标
- `missing_evidence`：现在还有哪些关键证据不够充分

## 5 分钟上手

1. 克隆并安装：
   ```bash
   git clone https://github.com/welcomemyworld/TradingAgents.git future-invest
   cd future-invest
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -e .
   ```
2. 设置你的模型提供方 key：
   ```bash
   export OPENAI_API_KEY=...
   ```
3. 启动产品：
   ```bash
   future-invest
   # or
   future-invest-web
   ```
4. 在 CLI 或 Web Control Room 里选择 provider、模型组合和 loop mode。

### 环境说明

建议把 Future Invest 安装在独立虚拟环境里。

如果你把它直接装进一个已经存在的 Anaconda 或研究环境里，`pip` 可能会提示 `streamlit`、`wrds`、`aext-*` 之类和当前环境已有包相关的冲突。那通常是环境混装问题，而不一定是 Future Invest 的打包本身有错。

最干净的路径是：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 模型提供方与 API 接入

Future Invest 采用 bring-your-own-provider 模式。  
简单理解就是：你自己决定接哪家的模型 API。

你可以根据自己的账号、额度和模型权限选择接入路径。

| Provider | `llm_provider` | `backend_url` | 认证 |
| --- | --- | --- | --- |
| OpenAI | `openai` | `https://api.openai.com/v1` | `OPENAI_API_KEY` |
| VectorEngine | `vectorengine` | `https://api.vectorengine.ai/v1` | `VECTORENGINE_API_KEY` 或 `OPENAI_API_KEY` |
| OpenRouter | `openrouter` | `https://openrouter.ai/api/v1` | `OPENROUTER_API_KEY` |
| Google | `google` | `https://generativelanguage.googleapis.com/v1` | `GOOGLE_API_KEY` |
| Anthropic | `anthropic` | `https://api.anthropic.com/` | `ANTHROPIC_API_KEY` |
| xAI | `xai` | `https://api.x.ai/v1` | `XAI_API_KEY` |
| Ollama | `ollama` | `http://localhost:11434/v1` | 本地运行时 |

配置示例：

```yaml
llm_provider: openai
backend_url: https://api.openai.com/v1
quick_think_llm: gpt-5-mini
deep_think_llm: gpt-5.4
institutional_loop_mode: lean
run_mode: hard_loop
selected_analysts:
  - business_truth
  - market_expectations
  - timing_catalyst
```

如果你的 provider 有 rate limit，先保持同样的 `lean` 配置重试，不要急着把流程加深。

## 它是怎么工作的

Future Invest 不是几位 analyst 简单拼起来的，而是尽量去模拟一个“能做投资决策的小型机构”。

这条流程故意保持很短，但每个阶段都对应一个很清晰的职责。  
下面按最容易理解的方式讲。

### 1. 先把问题定义清楚

一轮运行不是从“直接分析这家公司”开始，而是从“我们到底要解决什么投资问题”开始。

这里会先定一些上下文，比如：

- 研究哪个 ticker
- 以哪个日期作为决策时点
- 这个仓位在组合里是核心仓、主题仓，还是战术仓
- 大概能承受多少风险
- 这次只跑精简流程，还是跑完整流程

原因很简单：  
Future Invest 不是想写一份通用公司分析，而是想输出一个对某个具体投资席位有意义的决策。

### 2. 三路并行做研究

接下来系统会并行运行三条不同角度的研究路径：

- `Business Truth`：这家公司、这个行业，真实发生了什么，生意到底好不好
- `Market Expectations`：市场现在已经预期了什么，价格里已经反映了什么
- `Timing & Catalysts`：为什么这个想法是“现在”值得看，而不是以后再看

把这三条分开，是为了避免系统过早把所有信息压成单一叙事。  
一条研究“现实是什么”，一条研究“市场已经 price 了什么”，一条研究“为什么是现在”。

### 3. 让系统自己正反辩论

当研究材料准备得差不多之后，Future Invest 不会立刻下结论，而是会进入结构化内部辩论。

- `Thesis Engine`：把最强的可投资逻辑搭起来
- `Challenge Engine`：专门攻击这个逻辑，并找反证
- `Investment Director`：把正反两边的观点收拢成最终判断

这是系统最核心的纪律性来源。  
它不会把“模型很自信”误当成“结论足够好”，而是先看这个想法能不能经得住反驳。

### 4. 形成一份真正能拿去讨论的决策包

主输出不是一篇 narrative memo，而是一份决策包。

这份决策包要尽量回答一组很实际的问题：

- 立场是什么
- 仓位应该多大
- 入场框架是什么
- 什么情况会让 thesis 失效
- 入场后应该持续监控什么
- 还有哪些关键证据仍然缺失

在 `lean` 模式下，这通常就是自然终点。  
系统已经做了足够多的工作，可以产出一个有立场、可复核、可监控的决策包。

### 5. 记住这次结果，并为以后复盘

这轮运行结束之后，系统不会把结果丢掉。  
Future Invest 会把 trace、预测残差和 case history 写回去，让后续运行可以在前面的基础上继续积累。

这也是 evaluation 发挥作用的地方。  
项目内置了可复现的测试路径和 batch evaluation，目标是判断工作流有没有提高决策质量，而不只是“写得像不像真的”。

### 6. 对更重要的仓位，进入完整流程

有些决策值得进入比 lean loop 更深的一层。

当一个仓位足够重要时，同一份前端决策包可以继续扩展到更完整的机构评审流程：

- execution planning
- upside capture logic
- downside guardrails
- portfolio fit
- capital allocation committee review

`full` 路径的意义不是默认增加仪式感，而是让更大、更复杂的仓位在不改变前端研究逻辑的前提下，走入更深的审查流程。

### 什么东西会越用越值钱

- institutional memory
- prediction ledgers
- run traces
- 面向可复现 case set 的 evaluation

## 交互入口

### CLI

```bash
future-invest
python -m cli.main
```

CLI 是主要操作面。你可以在这里选择：

- provider 和模型组合
- lean / full loop 深度
- capability 组合
- mandate 强度和运行姿态

为了兼容旧路径，legacy CLI alias 仍然存在，但产品表层名称已经是 Future Invest。

### Web Control Room

```bash
future-invest-web
# or
python -m futureinvest_web.app
```

然后打开 `http://127.0.0.1:8000`。

Web Control Room 和 CLI 使用同一套 runtime。  
区别只是：Web 会把结果渲染成一个更容易浏览的机构决策界面，同时保留可选的 full committee path。

## Evaluation

Future Invest 带了一条 batch evaluation 路径，用来衡量 workflow 质量。

在仓库根目录运行公开面的 smoke tests：

```bash
python -m unittest \
  tests.test_investment_orchestration \
  tests.test_state_schema_consolidation \
  tests.test_evaluation_harness \
  tests.test_institutional_memory
```

更完整的实验入口见：

- [PROJECT_INDEX.md](PROJECT_INDEX.md)
- [evaluation/README.md](evaluation/README.md)
- [docs/future-invest-proposal.md](docs/future-invest-proposal.md)

## Python 使用方式

Future Invest 用 LangGraph 来组织整个流程，这样每个阶段都比较模块化，也更方便检查和调整。

公开品牌叫 Future Invest，但当前 Python package 路径仍然保留 `tradingagents`，这是为了兼容性。

示例：

```python
from tradingagents.graph.trading_graph import FutureInvestGraph
from tradingagents.default_config import DEFAULT_CONFIG

graph = FutureInvestGraph(debug=True, config=DEFAULT_CONFIG.copy())
_, decision = graph.propagate("NVDA", "2026-01-15")
print(decision)
```

你可以通过 runtime config 调整：

- provider 和 backend URL
- quick / deep 模型组合
- capability 选择
- debate 深度
- lean / full institutional loop mode

完整配置面见 `tradingagents/default_config.py`。

## 仓库导航

- [PROJECT_INDEX.md](PROJECT_INDEX.md)：最快找到关键文件的入口
- [docs/future-invest-proposal.md](docs/future-invest-proposal.md)：proposal 风格说明
- [docs/future-invest-pitch-memo.md](docs/future-invest-pitch-memo.md)：偏 pitch 的定位备忘录
- [docs/github-launch-checklist.md](docs/github-launch-checklist.md)：发布检查清单
- [docs/github-upload-guide.md](docs/github-upload-guide.md)：哪些内容该提交、哪些不该提交

## Contributing

最有价值的贡献通常落在这些层面：

- institution design
- research quality
- decision protocol quality
- evaluation quality
- operator experience

## Citation

如果你基于 Future Invest 继续构建，请引用这个仓库：

```bibtex
@software{futureinvest2026,
  author = {{Future Invest Project}},
  title = {Future Invest: AI-Native Institution Operating System},
  year = {2026},
  url = {https://github.com/welcomemyworld/TradingAgents},
  note = {GitHub repository}
}
```
