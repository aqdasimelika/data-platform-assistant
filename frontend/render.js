const API_BASE = 'http://127.0.0.1:5000';
const USER_ID = 'guest';

const chatMessages = document.getElementById('chat-messages');
const chatInputArea = document.getElementById('chat-input-area');
const backButton = document.getElementById('back-button');
const restartButton = document.getElementById('restart-button');
const userRoleEl = document.getElementById('user-role');
const usernameEl = document.getElementById('username');

let currentNode = null;
let currentPage = 1;
let pageSize = 3;
let searchResultsBox = null;
let isRestarting = false;





/* ---------------- API ---------------- */

async function api(path, data = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  if (!res.ok) throw new Error('API ERROR');
  return res.json();
}

/* ---------------- INIT ---------------- */

async function init() {
  try {
    const roleRes = await api('/role_detect', {});
    userRoleEl.textContent = roleRes.role;
    usernameEl.textContent = roleRes.username;

    const startRes = await api('/start', {
      user_id: USER_ID,
      role: roleRes.role
    });

    renderNode(startRes.node);
  } catch (e) {
    addBot(' خطا در اتصال به سرور');
    console.error(e);
  }
}

/* ---------------- RENDER ---------------- */

async function renderNode(node) {
  currentNode = node;
  chatInputArea.innerHTML = '';
  currentNodeId = node.id || currentNodeId;
  currentPage = 1;

  // نمایش متن
  if (node.text) {
    addBot(node.text);
  }

  // ⬅️ نودهای خودکار (message + solution)
  if (!isRestarting &&(node.type === 'message' || node.type === 'solution') && node.next 
  && node.type !== 'ticket' 
    )

   {
    setTimeout(async () => {
      const nextNode = await api('/faq', {
        user_id: USER_ID,
        action: 'get',
        node: node.next
      });
      renderNode(nextNode);
    }, 400);
    return;
  }

  // select
  if (node.type === 'select' && node.options) {
    currentPage = 1;
  renderOptions(
    node.options.slice(0, node.maxVisibleOptions || node.options.length),
    node
  );
  }

  renderSearchBox(node);

  // confirm
  if (node.type === 'confirm') {
    renderOptions([
      { label: 'بله', next: node.yes },
      { label: 'خیر', next: node.no }
    ], node);
  }

  // input
  if (node.type === 'input') {
    renderInput(node);
  }

if (node.type === 'ticket') {
  isRestarting = true;
  addBot(node.text || 'در حال ثبت تیکت...');

  try {
    const res = await api('/ticket/confirm', {
      user_id: USER_ID
    });

    addBot('تیکت با موفقیت ثبت شد');
    // console.log('TICKET SAVED:', res.ticket);
    renderRestartConfirm();
  } catch (e) {
    addBot('خطا در ثبت تیکت');
    console.error(e);
  }
    
    return;
  }

  // end
  if (node.type === 'end') {
    addBot('گفتگو به پایان رسید ');
  }
}



function renderOptions(options, node) {
  const box = document.createElement('div');
  box.className = 'options-container';

  options.forEach(op => {
    const btn = document.createElement('button');
    btn.className = 'option-button';
    btn.textContent = op.label;
    btn.onclick = () => {
      if (op.node) {
        selectSearchResult(op);
      } else {
        selectOption(op);
      }
};

    box.appendChild(btn);
  });

  chatInputArea.appendChild(box);

  //  Load More
  if (node.maxVisibleOptions && options.length >= node.maxVisibleOptions) {
    const moreBtn = document.createElement('button');
    moreBtn.className = 'load-more';
    moreBtn.textContent = 'موارد بیشتر';

    moreBtn.onclick = async () => {
      currentPage++;

      const res = await api('/faq', {
        user_id: USER_ID,
        action: 'load_more',
        node: node.id,
        page: currentPage
      });

      if (res.options && res.options.length) {
        renderOptions(res.options, node);
      } else {
        moreBtn.remove();
      }
    };

    chatInputArea.appendChild(moreBtn);
  }
}


function renderInput(node) {
  const input = document.createElement('input');
  input.className = 'input-field';
  input.placeholder = 'اینجا بنویسید...';

  const btn = document.createElement('button');
  btn.className='send';
  btn.textContent = 'ارسال';
  btn.onclick = async () => {
  if (!input.value.trim()) return;

  addUser(input.value);

  const res = await api('/faq', {
    user_id: USER_ID,
    action: 'input',
    node: node.id,        // ✅ حتماً ID نود
    value: input.value,
    next: node.next
  });

  renderNode(res);
};
  chatInputArea.appendChild(input);
  chatInputArea.appendChild(btn);
}

function renderConfirm(node) {
  const yes = document.createElement('button');
  const no = document.createElement('button');

  yes.textContent = 'بله';
  no.textContent = 'خیر';

  yes.onclick = () => selectOption({ label: 'بله', next: node.yes });
  no.onclick = () => selectOption({ label: 'خیر', next: node.no });

  chatInputArea.append(yes, no);
}


function renderRestartOnly() {
  const btn = document.createElement('button');
  btn.className = 'option-button';
  btn.textContent = 'شروع مجدد';

  btn.onclick = async () => {
    chatMessages.innerHTML = '';
    const res = await api('/faq', {
      user_id: USER_ID,
      action: 'restart'
    });
    renderNode(res);
  };

  chatInputArea.appendChild(btn);
}


/* ---------------- ACTIONS ---------------- */

async function selectOption(option) {
  addUser(option.label);

  const res = await api('/faq', {
    user_id: USER_ID,
    action: 'select',
    selected: {
      label: option.label,
      next: option.next
    },
    from_node: currentNode.id   
  });

  renderNode(res);
}


function renderSearchBox(node) {
  if (!node) return;

  if (['input', 'ticket', 'end', 'message', 'solution', 'confirm'].includes(node.type)) {
    clearSearchResults();

    const existing = document.getElementById('search-box');
    if (existing) existing.remove();

    return;
  }

  // اگر سرچ باکس از قبل هست، دوباره نساز
  let existing = document.getElementById('search-box');
  if (existing) return;

  const input = document.createElement('input');
  input.id = 'search-box';
  input.className = 'input-field';
  input.placeholder = 'جستجو...';

  input.oninput = async () => {
    const q = input.value.trim();

    clearSearchResults();
    if (!q) return;

    const res = await api('/search', {
      user_id: USER_ID,
      query: q
    });
    renderSearchResults(res.results || []);
  };
  chatInputArea.prepend(input);
}

function clearSearchResults() {
  if (searchResultsBox) {
    searchResultsBox.remove();
    searchResultsBox = null;
  }
}

function renderSearchResults(results) {
  clearSearchResults(); 

  searchResultsBox = document.createElement('div');
  searchResultsBox.className = 'options-container search-results';

  if (!results.length) {
    const msg = document.createElement('div');
    msg.className = 'message message-bot';
    msg.textContent = '❗ موردی پیدا نشد، لطفاً مراحل را طی کنید';
    searchResultsBox.appendChild(msg);
  } else {
    results.forEach(item => {
      const btn = document.createElement('button');
      btn.className = 'option-button';
      btn.textContent = item.title;

      btn.onclick = () => selectSearchResult(item);
      searchResultsBox.appendChild(btn);
    });
  }

  chatInputArea.appendChild(searchResultsBox);
}

async function selectSearchResult(item) {
  clearSearchResults();
  const searchBox = document.getElementById('search-box');
  if (searchBox) searchBox.value = '';
  addUser(item.title);
  const res = await api('/faq', {
    user_id: USER_ID,
    action: 'select',
    from_node: currentNode.id,
    selected: {
      label: item.title,
      next: item.node,
      path: item.path  //  مسیر از نتایج جستجو ارسال شود
    }
  });
  renderNode(res);
}


function renderRestartConfirm() {
  chatInputArea.innerHTML = '';
  
  // اضافه کردن کانتینر برای صفحه آخر
  const endContainer = document.createElement('div');
  endContainer.className = 'end-page-container';
  
  // دکمه شروع مجدد
  const yesBtn = document.createElement('button');
  yesBtn.className = 'option-button restart-btn';
  yesBtn.textContent = 'شروع مجدد';
  yesBtn.onclick = async () => {
    isRestarting = false;
    chatMessages.innerHTML = '';
    const res = await api('/faq', {
      user_id: USER_ID,
      action: 'restart'
    });
    renderNode(res);
    backButton.disabled = false;
    restartButton.disabled = false;
  };
  
  // دکمه پایان
  const noBtn = document.createElement('button');
  noBtn.className = 'option-button end-btn secondary';
  noBtn.textContent = 'پایان';
  noBtn.onclick = () => {
    addBot('گفتگو پایان یافت ');
    chatInputArea.innerHTML = '';
    backButton.disabled = true;
    restartButton.disabled = true;
  };
  
  // اضافه کردن دکمه‌ها به کانتینر
  const buttonContainer = document.createElement('div');
  buttonContainer.className = 'end-buttons-container';
  buttonContainer.appendChild(yesBtn);
  buttonContainer.appendChild(noBtn);
  
  endContainer.appendChild(buttonContainer);
  chatInputArea.appendChild(endContainer);
}

async function loadMore(node) {
  currentPage++;

  const res = await api('/faq', {
    user_id: USER_ID,
    action: 'load_more',
    node: node.id,
    page: currentPage
  });

  renderOptions(res.items, node);
}




/* ---------------- UI ---------------- */

function addBot(text) {
  const div = document.createElement('div');
  div.className = 'message message-bot';
  div.textContent = text;
  chatMessages.appendChild(div);
  scrollDown();
}

function addUser(text) {
  const div = document.createElement('div');
  div.className = 'message message-user';
  div.textContent = text;
  chatMessages.appendChild(div);
  scrollDown();
}

function scrollDown() {
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

/* ---------------- NAV ---------------- */

backButton.onclick = async () => {
  const res = await api('/faq', {
    user_id: USER_ID,
    action: 'back'
  });
  renderNode(res);
};

restartButton.onclick = async () => {
  // ریست کامل state
  chatMessages.innerHTML = '';
  chatInputArea.innerHTML = '';
  currentNode = null;
  currentPage = 1;

  const res = await api('/faq', {
    user_id: USER_ID,
    action: 'restart'
  });

  renderNode(res);
};


document.addEventListener('DOMContentLoaded', init);
