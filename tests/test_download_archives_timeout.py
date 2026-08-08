import unittest
from unittest.mock import MagicMock, patch, mock_open
import sys
import gzip

# Inject a mock requests module if missing
if 'requests' not in sys.modules:
    sys.modules['requests'] = MagicMock()

import download_archives

class TestDownloadArchivesTimeout(unittest.TestCase):
    @patch('requests.get')
    @patch('os.makedirs')
    @patch('builtins.open', new_callable=mock_open)
    @patch('re.findall')
    def test_requests_get_has_timeout(self, mock_findall, mock_file, mock_makedirs, mock_get):
        # Setup mock data
        mock_findall.return_value = ['test.txt.gz']

        mock_response = MagicMock()
        mock_response.content = gzip.compress(b"some content with metapost")
        mock_get.return_value = mock_response

        # Run the function
        download_archives.download_archives()

        # Check if requests.get was called with timeout
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertIn('timeout', kwargs)
        self.assertEqual(kwargs['timeout'], 10)

if __name__ == '__main__':
    unittest.main()
