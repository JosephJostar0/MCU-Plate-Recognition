declare namespace API {
  type LoginRequest = {
    /** Password */
    password: string;
    /** Uname */
    uname: string;
  };

  type PlateAddRequest = {
    /** Access */
    // access: number;
    /** Number */
    number: string;
    /** Period */
    // period: number;
  };

  type PlateCheckRequest = {
    /** Number */
    number: string;
  };

  type PlateDeleteRequest = {
    /** Pid */
    pid: number;
  };

  type PlateUpdateRequest = {
    /** Access */
    access: number;
    /** Number */
    number: string;
    /** Period */
    period: number;
    /** Pid */
    pid: number;
  };

  type ValidationErrorModel = {
    /** Error context an optional object which contains values required to render the error message. */
    ctx?: any;
    /** Location the error's location as a list.  */
    loc?: any;
    /** Message a computer-readable identifier of the error type. */
    msg?: any;
    /** Error Type a human readable explanation of the error. */
    type_?: any;
  };
}
