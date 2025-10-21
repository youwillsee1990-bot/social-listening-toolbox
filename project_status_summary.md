# 项目交接与状态总结

**最后更新时间:** 2025-10-20

## 1. 项目目标

创建一个名为 `social_listening_toolbox` 的命令行工具，用于分析社交媒体平台（Reddit, YouTube等）上的用户反馈，以识别和量化“问题”、“痛点”以及“正面反馈”，为内容创作和市场研究提供数据支持。

## 2. 当前文件结构

项目位于 `/home/youwillsee1990/social_listening_toolbox/`

```
social_listening_toolbox/
├── analyzer.py             # 主程序入口，负责解析命令
├── config.ini              # (用户自行创建) 存放API密钥
├── config.template.ini     # API密钥的模板文件
├── README.md               # 项目说明书（已更新）
├── requirements.txt        # Python依赖库
└── src/                    # 源代码目录
    ├── __init__.py
    ├── reddit_analyzer.py    # Reddit分析模块
    └── youtube_analyzer.py   # YouTube分析模块
```

## 3. 模块状态与开发计划

### Reddit分析模块
*   **状态:** :white_check_mark: **功能完成**
*   **能力:** 能够连接Reddit API，抓取指定Subreddit的热门帖子，调用AI分析内容，并将识别出的问题和痛点（中文）输出到CSV文件。

### YouTube分析模块
*   **状态:** :construction: **框架已搭建，核心逻辑待开发**
*   **已实现功能:**
    *   通过 `config.ini` 连接到YouTube Data API v3。
    *   能够通过 `--channel_url` 或 `--channel_id` 参数定位频道。
*   **下一步开发计划 (核心逻辑):**
    1.  **获取视频列表:** 从指定的频道ID获取所有视频的ID、标题和统计数据（观看数、点赞数、评论数）。
    2.  **智能筛选:** 从所有视频中，根据观看次数等标准，筛选出最重要的一部分进行分析（例如，最热门的10个视频）。
    3.  **获取评论:** 针对筛选出的每个视频，获取其“热门评论”和“最新评论”。
    4.  **升级AI分析指令:** 更新 `utils.py` 中的 `analyze_post_with_gemini` 函数，使其能够识别并分类出 **正面反馈 (Praise)**, **问题 (Question)**, **建议 (Suggestion)**, 和 **负面评价 (Pain Point)**。
    5.  **整合AI分析流程:** 遍历筛选后的视频和评论，调用AI进行分析。
    6.  **生成报告:** 将所有分析结果（视频信息、评论原文、评论分类、内容摘要、标签）汇总并存入指定的CSV输出文件。

### Discover (发现) 模块
*   **状态:** :memo: **已规划，待开发**
*   **目标:** 创建一个新的 `discover` 命令，允许用户输入一个关键词（如 "AI绘画"），工具将返回该领域内最受欢迎的YouTube频道列表（按订阅数排序），作为后续深入分析的目标。

## 4. 已知问题与解决方案
*   **问题:** 直接使用YouTube API的 `search.list` 功能来按名称查找频道，可能会因为新项目的API配额限制而被拒绝（403 Forbidden）。
*   **当前解决方案:** 工具已支持 `--channel_id` 参数。用户可以手动查找目标频道的ID，并直接提供给工具，从而绕过受限的搜索功能。