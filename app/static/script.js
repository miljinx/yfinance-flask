window.addEventListener('DOMContentLoaded', function (event) {
  handleClickFind()
  handleClickDownload()
})

function handleClickFind () {
  var form = document.getElementById('find-form')
  if (form === null) return
  form.addEventListener('submit', function () {
    var submitBtn = document.getElementById('find')
    submitBtn.setAttribute('disabled', '')
    submitBtn.setAttribute('value', 'Finding...')
  })
}

// TODO use fetch api for callback functionality
// see https://blog.logrocket.com/programmatic-file-downloads-in-the-browser-9a5186298d5c/
function handleClickDownload () {
  var form = document.getElementById('download-form')
  if (form === null) return
  var submitTimeout = 10
  form.addEventListener('submit', function () {
    var submitBtn = document.getElementById('download')
    submitBtn.setAttribute('disabled', '')
    submitBtn.setAttribute('value', 'Downloading...')
    window.setTimeout(function () {
      submitBtn.removeAttribute('disabled')
      submitBtn.setAttribute('value', 'Download')
    }, 1000 * submitTimeout)
  })
}
