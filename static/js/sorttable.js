/*
  SortTable — modified for ERP
  - 3-click cycle: asc → desc → original order
  - Bootstrap Icons (bi-sort-down, bi-sort-up, bi-arrow-down-up)
  - cursor:pointer on sortable headers
  - original order stored as data attribute on tbody
  Original: Stuart Langridge, http://www.kryogenix.org/code/browser/sorttable/
*/

var stIsIE = /*@cc_on!@*/false;

sorttable = {
  init: function() {
    if (arguments.callee.done) return;
    arguments.callee.done = true;
    if (_timer) clearInterval(_timer);
    if (!document.createElement || !document.getElementsByTagName) return;

    sorttable.DATE_RE = /^(\d\d?)[\/\.-](\d\d?)[\/\.-]((\d\d)?\d\d)$/;

    forEach(document.getElementsByTagName('table'), function(table) {
      if (table.className.search(/\bsortable\b/) != -1) {
        sorttable.makeSortable(table);
      }
    });
  },

  makeSortable: function(table) {
    if (table.getElementsByTagName('thead').length == 0) {
      the = document.createElement('thead');
      the.appendChild(table.rows[0]);
      table.insertBefore(the, table.firstChild);
    }
    if (table.tHead == null) table.tHead = table.getElementsByTagName('thead')[0];
    if (table.tHead.rows.length != 1) return;

    sortbottomrows = [];
    for (var i = 0; i < table.rows.length; i++) {
      if (table.rows[i].className.search(/\bsortbottom\b/) != -1) {
        sortbottomrows[sortbottomrows.length] = table.rows[i];
      }
    }
    if (sortbottomrows) {
      if (table.tFoot == null) {
        tfo = document.createElement('tfoot');
        table.appendChild(tfo);
      }
      for (var i = 0; i < sortbottomrows.length; i++) {
        tfo.appendChild(sortbottomrows[i]);
      }
      delete sortbottomrows;
    }

    headrow = table.tHead.rows[0].cells;
    for (var i = 0; i < headrow.length; i++) {
      if (!headrow[i].className.match(/\bsorttable_nosort\b/)) {
        mtch = headrow[i].className.match(/\bsorttable_([a-z0-9]+)\b/);
        if (mtch) { override = mtch[1]; }
        if (mtch && typeof sorttable["sort_" + override] == 'function') {
          headrow[i].sorttable_sortfunction = sorttable["sort_" + override];
        } else {
          headrow[i].sorttable_sortfunction = sorttable.guessType(table, i);
        }
        headrow[i].sorttable_columnindex = i;
        headrow[i].sorttable_tbody = table.tBodies[0];
        headrow[i].style.cursor = 'pointer';

        dean_addEvent(headrow[i], "click", sorttable.innerSortFunction = function(e) {
          var col = this.sorttable_columnindex;
          var tb = this.sorttable_tbody;
          var rows = tb.rows;

          // Store original order on first sort
          if (!tb.hasAttribute('data-original-order')) {
            var orig = [];
            for (var j = 0; j < rows.length; j++) {
              orig.push(rows[j].id || '');
            }
            tb.setAttribute('data-original-order', JSON.stringify(orig));
          }

          // Check current sort state
          var isSorted = this.className.search(/\bsorttable_sorted\b/) != -1;
          var isSortedReverse = this.className.search(/\bsorttable_sorted_reverse\b/) != -1;

          // Clear all sorted classes and indicators in header
          theadrow = this.parentNode;
          forEach(theadrow.childNodes, function(cell) {
            if (cell.nodeType == 1) {
              cell.className = cell.className.replace(/\bsorttable_sorted(_reverse)?\b/g, '');
              var ind = cell.querySelector('.sort-indicator');
              if (ind) ind.parentNode.removeChild(ind);
            }
          });

          if (!isSorted && !isSortedReverse) {
            // 1st click: ascending
            this.className += ' sorttable_sorted';
            row_array = [];
            for (var j = 0; j < rows.length; j++) {
              row_array[row_array.length] = [sorttable.getInnerText(rows[j].cells[col]), rows[j]];
            }
            row_array.sort(this.sorttable_sortfunction);
            for (var j = 0; j < row_array.length; j++) {
              tb.appendChild(row_array[j][1]);
            }
            delete row_array;
            var ind = document.createElement('span');
            ind.className = 'sort-indicator ms-1 bi bi-sort-down';
            this.appendChild(ind);
          } else if (isSorted && !isSortedReverse) {
            // 2nd click: descending
            this.className += ' sorttable_sorted_reverse';
            sorttable.reverse(tb);
            var ind = document.createElement('span');
            ind.className = 'sort-indicator ms-1 bi bi-sort-up';
            this.appendChild(ind);
          } else {
            // 3rd click: restore original order
            var origOrder = JSON.parse(tb.getAttribute('data-original-order') || '[]');
            if (origOrder.length > 0) {
              var rowMap = {};
              for (var j = 0; j < rows.length; j++) {
                rowMap[rows[j].id || ''] = rows[j];
              }
              for (var j = 0; j < origOrder.length; j++) {
                if (rowMap[origOrder[j]]) {
                  tb.appendChild(rowMap[origOrder[j]]);
                }
              }
            }
            var ind = document.createElement('span');
            ind.className = 'sort-indicator ms-1 bi bi-arrow-down-up';
            this.appendChild(ind);
          }
        });
      }
    }
  },

  guessType: function(table, column) {
    sortfn = sorttable.sort_alpha;
    for (var i = 0; i < table.tBodies[0].rows.length; i++) {
      text = sorttable.getInnerText(table.tBodies[0].rows[i].cells[column]);
      if (text != '') {
        if (text.match(/^-?[ $€]?[\d,.]+%?$/)) {
          return sorttable.sort_numeric;
        }
        possdate = text.match(sorttable.DATE_RE);
        if (possdate) {
          first = parseInt(possdate[1]);
          second = parseInt(possdate[2]);
          if (first > 12) {
            return sorttable.sort_ddmm;
          } else if (second > 12) {
            return sorttable.sort_mmdd;
          } else {
            sortfn = sorttable.sort_ddmm;
          }
        }
      }
    }
    return sortfn;
  },

  getInnerText: function(node) {
    if (!node) return "";
    hasInputs = (typeof node.getElementsByTagName == 'function') &&
                 node.getElementsByTagName('input').length;
    if (node.getAttribute("sorttable_customkey") != null) {
      return node.getAttribute("sorttable_customkey");
    } else if (typeof node.textContent != 'undefined' && !hasInputs) {
      return node.textContent.replace(/^\s+|\s+$/g, '');
    } else if (typeof node.innerText != 'undefined' && !hasInputs) {
      return node.innerText.replace(/^\s+|\s+$/g, '');
    } else if (typeof node.text != 'undefined' && !hasInputs) {
      return node.text.replace(/^\s+|\s+$/g, '');
    } else {
      switch (node.nodeType) {
        case 3:
          if (node.nodeName.toLowerCase() == 'input') {
            return node.value.replace(/^\s+|\s+$/g, '');
          }
        case 4:
          return node.nodeValue.replace(/^\s+|\s+$/g, '');
          break;
        case 1:
        case 11:
          var innerText = '';
          for (var i = 0; i < node.childNodes.length; i++) {
            innerText += sorttable.getInnerText(node.childNodes[i]);
          }
          return innerText.replace(/^\s+|\s+$/g, '');
          break;
        default:
          return '';
      }
    }
  },

  reverse: function(tbody) {
    newrows = [];
    for (var i = 0; i < tbody.rows.length; i++) {
      newrows[newrows.length] = tbody.rows[i];
    }
    for (var i = newrows.length - 1; i >= 0; i--) {
      tbody.appendChild(newrows[i]);
    }
    delete newrows;
  },

  /* sort functions */
  sort_priority: function(a, b) {
    var PRIORITY_ORDER = { "bassa": 1, "media": 2, "alta": 3, "urgente": 4 };
    var va = PRIORITY_ORDER[a[0].toLowerCase().trim()] ?? 999;
    var vb = PRIORITY_ORDER[b[0].toLowerCase().trim()] ?? 999;
    return va - vb;
  },
  sort_numeric: function(a, b) {
    aa = parseFloat(a[0].replace(/[^0-9.-]/g, ''));
    if (isNaN(aa)) aa = 0;
    bb = parseFloat(b[0].replace(/[^0-9.-]/g, ''));
    if (isNaN(bb)) bb = 0;
    return aa - bb;
  },
  sort_alpha: function(a, b) {
    if (a[0] == b[0]) return 0;
    if (a[0] < b[0]) return -1;
    return 1;
  },
  sort_ddmm: function(a, b) {
    mtch = a[0].match(sorttable.DATE_RE);
    y = mtch[3]; m = mtch[2]; d = mtch[1];
    if (m.length == 1) m = '0' + m;
    if (d.length == 1) d = '0' + d;
    dt1 = y + m + d;
    mtch = b[0].match(sorttable.DATE_RE);
    y = mtch[3]; m = mtch[2]; d = mtch[1];
    if (m.length == 1) m = '0' + m;
    if (d.length == 1) d = '0' + d;
    dt2 = y + m + d;
    if (dt1 == dt2) return 0;
    if (dt1 < dt2) return -1;
    return 1;
  },
  sort_mmdd: function(a, b) {
    mtch = a[0].match(sorttable.DATE_RE);
    y = mtch[3]; d = mtch[2]; m = mtch[1];
    if (m.length == 1) m = '0' + m;
    if (d.length == 1) d = '0' + d;
    dt1 = y + m + d;
    mtch = b[0].match(sorttable.DATE_RE);
    y = mtch[3]; d = mtch[2]; m = mtch[1];
    if (m.length == 1) m = '0' + m;
    if (d.length == 1) d = '0' + d;
    dt2 = y + m + d;
    if (dt1 == dt2) return 0;
    if (dt1 < dt2) return -1;
    return 1;
  }
};

/* --- Supporting functions --- */

if (document.addEventListener) {
  document.addEventListener("DOMContentLoaded", sorttable.init, false);
}

/*@cc_on @*/
/*@if (@_win32)
  document.write("<script id=__ie_onload defer src=javascript:void(0)><\/script>");
  var script = document.getElementById("__ie_onload");
  script.onreadystatechange = function() {
    if (this.readyState == "complete") {
      sorttable.init();
    }
  };
/*@end @*/

if (/WebKit/i.test(navigator.userAgent)) {
  var _timer = setInterval(function() {
    if (/loaded|complete/.test(document.readyState)) {
      sorttable.init();
    }
  }, 10);
}

window.onload = sorttable.init;

function dean_addEvent(element, type, handler) {
  if (element.addEventListener) {
    element.addEventListener(type, handler, false);
  } else {
    if (!handler.$$guid) handler.$$guid = dean_addEvent.guid++;
    if (!element.events) element.events = {};
    var handlers = element.events[type];
    if (!handlers) {
      handlers = element.events[type] = {};
      if (element["on" + type]) {
        handlers[0] = element["on" + type];
      }
    }
    handlers[handler.$$guid] = handler;
    element["on" + type] = handleEvent;
  }
}
dean_addEvent.guid = 1;

function removeEvent(element, type, handler) {
  if (element.removeEventListener) {
    element.removeEventListener(type, handler, false);
  } else {
    if (element.events && element.events[type]) {
      delete element.events[type][handler.$$guid];
    }
  }
}

function handleEvent(event) {
  var returnValue = true;
  event = event || fixEvent(((this.ownerDocument || this.document || this).parentWindow || window).event);
  var handlers = this.events[event.type];
  for (var i in handlers) {
    this.$$handleEvent = handlers[i];
    if (this.$$handleEvent(event) === false) {
      returnValue = false;
    }
  }
  return returnValue;
}

function fixEvent(event) {
  event.preventDefault = fixEvent.preventDefault;
  event.stopPropagation = fixEvent.stopPropagation;
  return event;
}
fixEvent.preventDefault = function() { this.returnValue = false; };
fixEvent.stopPropagation = function() { this.cancelBubble = true; };

if (!Array.forEach) {
  Array.forEach = function(array, block, context) {
    for (var i = 0; i < array.length; i++) {
      block.call(context, array[i], i, array);
    }
  };
}

Function.prototype.forEach = function(object, block, context) {
  for (var key in object) {
    if (typeof this.prototype[key] == "undefined") {
      block.call(context, object[key], key, object);
    }
  }
};

String.forEach = function(string, block, context) {
  Array.forEach(string.split(""), function(chr, index) {
    block.call(context, chr, index, string);
  });
};

var forEach = function(object, block, context) {
  if (object) {
    var resolve = Object;
    if (object instanceof Function) {
      resolve = Function;
    } else if (object.forEach instanceof Function) {
      object.forEach(block, context);
      return;
    } else if (typeof object == "string") {
      resolve = String;
    } else if (typeof object.length == "number") {
      resolve = Array;
    }
    resolve.forEach(object, block, context);
  }
};
