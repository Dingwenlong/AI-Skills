---
name: wedoc-smartsheet-change-recorder
description: 将 Common/API/配置异动记录写入企业微信文档智能表格 WebHook。用于读取本地异动清单 Excel 的表头与示例写法，按字段 schema 生成 add_records 或 update_records payload，写入備註、調整內容、調整日期、調整人、所屬類型、調整接口等字段，并按企业微信成员字段规则处理人员姓名/别名或 user_id。
---

# 企业微信智能表格异动记录写入

用于把本地异动清单 Excel 的既有格式转换为企业微信文档智能表格 WebHook payload，并提交新增或更新记录。

## 适用场景

- 用户给出 `Common異動清單.xlsx`、类似异动清单、WebHook 地址和本次改动内容。
- 需要把 CommonUtil / CommonFunc / appsetting / API 等调整录入智能表格。
- 需要根据返回的 `record_id` 追加更新某个字段，例如补 `調整人(人员)`。

## 工作流

1. 读取附件 Excel 第一行表头和已有数据，确认字段写法。
2. 按用户给的 WebHook schema 映射字段 ID：
   - `fwsRq0`: `備註`
   - `fbPZt1`: `調整內容`
   - `fm3WC4`: `調整日期`
   - `fa80iy`: `調整人(人员)`
   - `fPWtj7`: `所屬類型`
   - `faSRWW`: `調整接口`
3. 按既有清单风格整理记录：
   - `備註` 写变更类型，例如 `變更公共方法`、`新追加公共方法`、`增加配置項`。
   - `調整內容` 用编号逐条写清楚，保留换行。
   - `調整日期` 转为北京时间当天 00:00:00 的毫秒时间戳字符串。
   - `所屬類型` 写 `CommonUtil` / `CommonFunc` / `appsetting` 等。
   - `調整接口` 写接口或配置名称。
4. 人员字段处理：
   - 若用户给企业微信真实 `user_id`，使用 userid 模式：`[{"user_id": "USERID"}]`。
   - 若用户只给姓名或别名，例如 `丁文龙(Jimmy)`，使用姓名/别名模式：`["丁文龙(Jimmy)"]`。
   - 不要把成员字段写成文本富文本对象，例如 `[{"type":"text","text":"..."}]`。
   - 不要猜测 user_id；若姓名/别名模式被接口拒绝，再提示需要企业微信真实 `user_id`。
5. 调用 WebHook 后检查 `errcode`：
   - `0` 表示成功，记录返回的 `record_id`。
   - 非 0 时回报错误码和 errmsg，不重复新增。

## 脚本

使用 `scripts/send_wedoc_change_records.py` 生成或提交 payload。

新增记录示例：

```powershell
python "C:\Users\jimmy\.codex\skills\wedoc-smartsheet-change-recorder\scripts\send_wedoc_change_records.py" `
  --webhook "<Webhook URL>" `
  --excel "C:\Users\jimmy\Desktop\Common異動清單.xlsx" `
  --records-json ".\records.json" `
  --date "2026/5/23" `
  --user-text "丁文龙(Jimmy)"
```

只生成 payload 不提交：

```powershell
python "...\send_wedoc_change_records.py" --webhook "<Webhook URL>" --records-json ".\records.json" --dry-run
```

更新既有记录人员字段：

```powershell
python "...\send_wedoc_change_records.py" `
  --webhook "<Webhook URL>" `
  --update-user-record-ids "BDh0ht,TmIZR7" `
  --user-text "丁文龙(Jimmy)"
```

`records.json` 格式：

```json
[
  {
    "note": "變更公共方法",
    "content": "1.調整內容...",
    "type": "CommonUtil",
    "api": "GetCommonCurrency"
  }
]
```

## 注意

- 不要把一次性 WebHook URL 固化到技能文件或脚本。
- 新增记录和更新记录都使用 `POST` 到工作表 WebHook 地址。
- WebHook 不支持写入公式、自动编号、查找引用、关联、创建人、创建时间、最后编辑人、最后编辑时间、群聊、文件字段。
- 成员字段支持姓名/别名模式和 userid 模式；`--user-text` 参数为兼容旧命名，实际输出姓名/别名字符串数组。
- 未提供人员时脚本保留示例兼容值 `[{"user_id": ""}]`，但正式写入前优先补姓名/别名或真实 user_id。
- 频率限制：每个工作表累计添加或更新记录不超过 3000 条/分钟；每个智能表格文档所有 WebHook 累计不超过 10000 条/分钟。
- 若已新增成功后发现人员字段不对，优先用 `update_records` 原地修正，不要重复新增。
- 每次提交后保留返回的 `record_id`，方便补正。
