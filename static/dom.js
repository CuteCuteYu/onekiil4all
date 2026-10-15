/**
 * 上古必斩必杀 DOM元素缓存
 */

const $messages = document.getElementById('messages');
const $input = document.getElementById('msg-input');
const $send = document.getElementById('btn-send');
const $btnStop = document.getElementById('btn-stop');
const $loading = document.getElementById('loading');
const $loadingText = document.getElementById('loading-text');
const $threadBadge = document.getElementById('thread-badge');
const $btnNew = document.getElementById('btn-new');
const $historyList = document.getElementById('history-list');
const $todoContent = document.getElementById('todo-content');
const $skillsList = document.getElementById('skills-list');
const $toolsList = document.getElementById('tools-list');
const $pendingQueue = document.getElementById('pending-queue');
const $pendingList = document.getElementById('pending-list');
const $btnClearPending = document.getElementById('btn-clear-pending');
const $btnRefreshHistory = document.getElementById('btn-refresh-history');
const $btnRefreshTodo = document.getElementById('btn-refresh-todo');
const $btnRefreshTrends = document.getElementById('btn-refresh-trends');
const $hotsearchList = document.getElementById('hotsearch-list');
const $alertsList = document.getElementById('alerts-list');
const $alertHistoryList = document.getElementById('alert-history-list');
const $alertInput = document.getElementById('alert-input');
const $alertUnreadBadge = document.getElementById('alert-unread-badge');
const $btnAddAlert = document.getElementById('btn-add-alert');
const $btnRefreshAlerts = document.getElementById('btn-refresh-alerts');
const $btnClearAlertHistory = document.getElementById('btn-clear-alert-history');
const $btnSearchLinks = document.getElementById('btn-search-links');
const $linkKeywordInput = document.getElementById('link-keyword-input');
const $linkResults = document.getElementById('link-results');
const $btnClearLinks = document.getElementById('btn-clear-links');
const $rssInput = document.getElementById('rss-input');
const $btnAddRss = document.getElementById('btn-add-rss');
const $rssSources = document.getElementById('rss-sources');
const $rssArticles = document.getElementById('rss-articles');
const $profileInput = document.getElementById('profile-input');
const $btnProfileSubmit = document.getElementById('btn-profile-submit');
const $btnProfileClear = document.getElementById('btn-profile-clear');
const $profileResult = document.getElementById('profile-result');