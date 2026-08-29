/**
 * 上古必斩必杀 全局状态
 * 各模块直接读写这些变量；待发送队列的操作在 chat.js 中
 */

let threadId = null;
let busy = false;
let pendingMessages = [];
let currentAbortController = null;
