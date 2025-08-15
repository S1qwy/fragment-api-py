from .models import FragmentAPIError, FragmentErrorType

class FragmentAuthError(FragmentAPIError):
    pass

class FragmentOrderError(FragmentAPIError):
    pass

class FragmentPaymentError(FragmentAPIError):
    pass

class FragmentNetworkError(FragmentAPIError):
    pass
