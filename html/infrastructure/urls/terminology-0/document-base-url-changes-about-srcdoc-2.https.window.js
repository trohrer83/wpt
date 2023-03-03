// META: script=/common/get-host-info.sub.js
//
// create non-srdoc iframe (grand-child), then update its URL to about:srcdoc
// using the document.open() trick: http://jsfiddle.net/int32_t/oztck57e/5/ .
// Update child's base URL. Check that srcdoc iframe's base URL did not change.

function start (child_document) {
  assert_not_equals(document, child_document);
  promise_test(async () => {
    assert_equals(child_document.URL, 'about:srcdoc');
    var grandchild_document =
        child_document.querySelector('iframe').contentDocument;
    console.log('BEFORE: grandchild URL = ' + grandchild_document.URL);
    try {
      grandchild_document.open('', '');
    } catch (e) {
      console.log(e);
    }
    grandchild_document =
        child_document.querySelector('iframe').contentDocument;

    // Debug logging.
    console.log('AFTER: grandchild URL = ' + grandchild_document.URL);
    console.log(
        'AFTER: grandchild baseURI = ' + grandchild_document.baseURI);
    console.log('AFTER: child URL = ' + child_document.URL);
    console.log('AFTER: child baseURI = ' + child_document.baseURI);

    assert_equals(grandchild_document.URL, 'about:srcdoc');

    // Given child a new baseURI.
    const original_child_baseURI = child_document.baseURI;
    console.log('child baseURI = ' + original_child_baseURI);
    const base_element = child_document.createElement('base');
    base_element.href = get_host_info().REMOTE_ORIGIN;
    child_document.head.appendChild(base_element);
    assert_not_equals(
        child_document.baseURI, original_child_baseURI,
        'parent baseURI failed to change.');

    // Verify grandchild's baseURI didn't change. It should have inherited the
    // child's original baseURI (i.e. at time the grandchild became srcdoc).
    assert_equals(original_child_baseURI, grandchild_document.baseURI);

    // Cleanup.
    child_document.querySelector('base').remove();
  }, 'non-srcdoc => srcdoc, parent changes baseURI');
  done();
}

// Create child in main frame.
const child_iframe = document.createElement('iframe');
document.body.appendChild(child_iframe);
child_iframe.srcdoc =
    '<iframe></iframe><script>parent.start(document)</script>';
