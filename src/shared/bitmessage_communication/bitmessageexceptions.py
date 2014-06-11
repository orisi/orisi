from collections import defaultdict

class BitmessageException(Exception):
  pass

class UnknownProtocolException(BitmessageException):
  pass

class NoParameterException(BitmessageException):
  pass

class BlankPassphraseException(BitmessageException):
  pass

class BlankPassphraseException(BitmessageException):
  pass

class ZeroAddressesException(BitmessageException):
  pass

class TooManyAddressesException(BitmessageException):
  pass

class CouldNotDecodeAddressException(BitmessageException):
  pass

class AddressChecksumFailedException(BitmessageException):
  pass

class InvalidCharactersInAddressException(BitmessageException):
  pass

class NotAccessibleAddressException(BitmessageException):
  pass

class DisabledAddressException(BitmessageException):
  pass

class InvalidAckdataLengthException(BitmessageException):
  pass

class AlreadySubscribedException(BitmessageException):
  pass

class InvalidBaseEncodingException(BitmessageException):
  pass

class ChanNameNotMatchingAddressException(BitmessageException):
  pass

class InvalidHashLengthException(BitmessageException):
  pass

class InvalidMethodException(BitmessageException):
  pass

class UnexpectedAPIFailureException(BitmessageException):
  pass

class DecodeErrorException(BitmessageException):
  pass

class BoolExpectedException(BitmessageException):
  pass

class ChanAlreadySubscribedException(BitmessageException):
  pass

RAW_EXCEPTION_API = {
  '0000': NoParameterException,
  '0001': BlankPassphraseException,
  '0004': ZeroAddressesException,
  '0005': TooManyAddressesException,
  '0007': CouldNotDecodeAddressException,
  '0008': AddressChecksumFailedException,
  '0009': InvalidCharactersInAddressException,
  '0013': NotAccessibleAddressException,
  '0014': DisabledAddressException,
  '0015': InvalidAckdataLengthException,
  '0016': AlreadySubscribedException,
  '0017': InvalidBaseEncodingException,
  '0018': ChanNameNotMatchingAddressException,
  '0019': InvalidHashLengthException,
  '0020': InvalidMethodException,
  '0021': UnexpectedAPIFailureException,
  '0022': DecodeErrorException,
  '0023': BoolExpectedException,
  '0024': ChanAlreadySubscribedException,
}

EXCEPTION_API = defaultdict(lambda: UnknownProtocolException, RAW_EXCEPTION_API)

