#define PY_SSIZE_T_CLEAN
#define SIZEINC 80
#define MAXDEPTH 10
#include <Python.h>

typedef struct tagRuleReturn
{
    Py_ssize_t pos;
    Py_ssize_t len;
    Py_UNICODE *text;
} RuleReturn;

typedef struct tagHooks
{
    PyObject *depth_exceed_msg;
    PyObject *rule_parser;
} Hooks;

const Py_UNICODE TOKEN_A = (Py_UNICODE)('-');
const Py_UNICODE TOKEN_B = (Py_UNICODE)('{');
const Py_UNICODE TOKEN_C = (Py_UNICODE)('}');

/*static UNISIZE parse_rule(Py_UNICODE *text);*/
static RuleReturn recursive_convert_rule (Py_UNICODE *text, Py_ssize_t pos,
                                          Py_ssize_t len, int depth, Hooks *hooks);
static PyObject *convert (PyObject *self, PyObject *args);

static RuleReturn recursive_convert_rule (Py_UNICODE *text, Py_ssize_t pos,
                                          Py_ssize_t len, int depth, Hooks *hooks)
{
    Py_ssize_t retlen; // the real length (allocated size) of the ret.text
    Py_ssize_t oripos = pos; // the original position
    RuleReturn ret; // the return structure
    int exceedtime = 0; // count exceed time
    
    ret.pos = pos;
    ret.len = 0;
    ret.text = PyMem_NEW(Py_UNICODE, SIZEINC);
    retlen = SIZEINC;
    
    
    while (ret.pos < len) {
        if (ret.pos + 1 < len) {
            if (text[ret.pos] == TOKEN_A && text[ret.pos + 1] == TOKEN_B) {
                if (depth < MAXDEPTH) {
                    RuleReturn ret2 = recursive_convert_rule(text, ret.pos + 2, len, depth + 1, hooks);
                    if (ret.len + ret2.len >= retlen) {
                        retlen += (ret2.len / SIZEINC + 1) * SIZEINC;
                        PyMem_RESIZE(ret.text, Py_UNICODE, retlen);
                    }
                    memcpy(ret.text + ret.len, ret2.text, ret2.len * sizeof(Py_UNICODE));
                    ret.pos = ret2.pos;
                    ret.len += ret2.len;
                    PyMem_DEL(ret2.text);
                    continue;
                }
                else {
                    if (!exceedtime && hooks->depth_exceed_msg != NULL) {
                        PyObject *depthobj = PyInt_FromLong(depth);
                        PyObject *msg = PyObject_CallFunctionObjArgs(hooks->depth_exceed_msg, depthobj, NULL);
                        Py_XDECREF(depthobj);
                        if (msg != NULL) {
	                        Py_ssize_t msglen = PyUnicode_GET_SIZE(msg);
	                        Py_UNICODE *msgtext = PyUnicode_AS_UNICODE(msg);
	                        if (ret.len + msglen >= retlen) {
	                            retlen += (msglen / SIZEINC + 1) * SIZEINC;
	                            PyMem_RESIZE(ret.text, Py_UNICODE, retlen);
	                        }
	                        memcpy(ret.text + ret.len, msgtext, msglen * sizeof(Py_UNICODE));
	                        ret.len += msglen;
                    	}
                    	Py_XDECREF(msg);
                    }
                    exceedtime ++;
                }
            }
            else if (text[ret.pos] == TOKEN_C && text[ret.pos + 1] == TOKEN_A) {
                if (depth >= MAXDEPTH && exceedtime) {
                    exceedtime --;
                }
                else {
                    PyObject *textobj;
                    PyObject *oldtextobj = PyUnicode_FromUnicode(ret.text, ret.len);
                    textobj = PyObject_CallFunctionObjArgs(hooks->rule_parser, oldtextobj, NULL);
                    Py_XDECREF(oldtextobj);
                    ret.pos += 2;
                    if (textobj != NULL) {
                        ret.len = PyUnicode_GET_SIZE(textobj);
                        PyMem_RESIZE(ret.text, Py_UNICODE, ret.len);
                        memcpy(ret.text, PyUnicode_AS_UNICODE(textobj), ret.len * sizeof(Py_UNICODE));
                    }
                    Py_XDECREF(textobj);
                    return ret;
                }
            }
        }
        if (ret.len + 1 >= retlen) {
            retlen += SIZEINC;
            PyMem_RESIZE(ret.text, Py_UNICODE, retlen);
        }
        ret.text[ret.len ++] = text[ret.pos ++];
    }
    // unclosed rule, won't parse but still auto convert
    ret.text[0] = TOKEN_A;
    ret.len = 1;
    ret.pos = -- oripos;
    return ret;
}

static PyObject *convert(PyObject *self, PyObject *args)
{
    // Input string
    Py_ssize_t inputlen; // input string length
    Py_ssize_t inputpos = 0; // input string position
    Py_UNICODE *input; // input string
    
    // Output string
    Py_ssize_t outputlen; // output string length
    Py_ssize_t outputlentest; // output length test, equals maxlen at first
    Py_ssize_t outputpos = 0; // output string position
    Py_UNICODE *output; // output string
    PyObject *ret; // output PyObject
    
    // langconv.Converter instance
    PyObject *converter;
    
    // Tables
    PyObject *convtable; // convert table
    PyObject *quicktable; // quick table
    
    // Hooks
    PyObject *hooksobj;
    Hooks hooks;
    
    //Parse rules?
    int parserules = 1;

    // Temp use
    int found; // a flag
    Py_ssize_t count_i;
    PyObject *single;
    PyObject *wordlens;
    Py_ssize_t lengthofwordlens;
    Py_ssize_t oriwordlen;
    PyObject *oriwordobj;
    PyObject *convwordobj;
    Py_UNICODE *convword;
    Py_ssize_t convwordlen;
    RuleReturn parsedtext;
    
    // retrieve arguments from Python
    if (!PyArg_ParseTuple(args, "Ou#|i", &converter, &input, &inputlen, &parserules))
        return NULL;
    
    // retrieve arguments from converter instance
    convtable = PyObject_GetAttrString(converter, "convtable");
    quicktable = PyObject_GetAttrString(converter, "quicktable");
    outputlentest = PyInt_AsSsize_t(PyObject_GetAttrString(converter, "maxlen"));
    
    // get hooks
    hooksobj = PyObject_GetAttrString(converter, "hooks");
    hooks.depth_exceed_msg = PyDict_GetItemString(hooksobj, "depth_exceed_msg");
    hooks.rule_parser = PyDict_GetItemString(hooksobj, "rule_parser");
    
    if (!PyCallable_Check(hooks.depth_exceed_msg)) {
        hooks.depth_exceed_msg = NULL;
    }
    if (!PyCallable_Check(hooks.rule_parser)) {
        hooks.rule_parser = NULL;
    }
        
    // initiate output string
    output = PyMem_NEW(Py_UNICODE, inputlen);
    outputlen = inputlen;

    while (inputpos < inputlen) {
        // Parse rules
        if (parserules && inputpos + 1 < inputlen) {
            if (input[inputpos] == TOKEN_A && input[inputpos + 1] == TOKEN_B) {
                // token found
                parsedtext = recursive_convert_rule(input, inputpos + 2, inputlen, 1, &hooks);
                inputpos = parsedtext.pos;
                outputlentest += parsedtext.len;
                if (outputlentest >= outputlen) {
                    outputlen += (parsedtext.len / SIZEINC + 1) * SIZEINC;
                    PyMem_RESIZE(output, Py_UNICODE, outputlen);
                }
                memcpy(output + outputpos, parsedtext.text, parsedtext.len * sizeof(Py_UNICODE));
                outputpos += parsedtext.len;
                PyMem_DEL(parsedtext.text);
                continue;
            }
        }
        // Check if current outputlen will be exceeded or not
        // if it will be, let's resize it to prevent this happen.
        if (outputlentest >= outputlen) {
            outputlen += SIZEINC;
            PyMem_RESIZE(output, Py_UNICODE, outputlen);
        }
        
        // retrieve a character from input for test
        single = PyUnicode_FromUnicode(input + inputpos, 1);
        wordlens = PyDict_GetItem(quicktable, single); // check quicktable
        Py_XDECREF(single); // release single
        
        if (wordlens == NULL) {
            // find nothing in quicktable, just append the character to output
            output[outputpos ++] = input[inputpos ++];
            outputlentest ++;
        }
        
        else {
            //return PyList_New(0);
            lengthofwordlens = PyList_Size(wordlens);
            found = 0;
            
            // let's test words from longest to shortest (quicktable is sorted)
            for (count_i = 0; count_i < lengthofwordlens; count_i ++) {
                oriwordlen = PyInt_AsSsize_t(PyList_GetItem(wordlens, count_i));
                oriwordobj = PyUnicode_FromUnicode(input + inputpos, (Py_ssize_t) oriwordlen);
                convwordobj = PyDict_GetItem(convtable, oriwordobj); // check convtable
                Py_XDECREF(oriwordobj); // release oriwordobj
                if (convwordobj != NULL) {
                    if (PyUnicode_Check(convwordobj)) {
                        // find one! now append it to output
                        convword = PyUnicode_AS_UNICODE(convwordobj);
                        convwordlen = PyUnicode_GET_SIZE(convwordobj);
                        memcpy(output + outputpos, convword, convwordlen * sizeof(Py_UNICODE));
                        outputpos += convwordlen;
                        outputlentest += convwordlen;
                        inputpos += oriwordlen;
                        found = 1; // mark as found
                        break;
                    }
                }
            }
            if (found == 0) {
                // find nothing, just append the character to output
                output[outputpos ++] = input[inputpos ++];
                outputlentest ++;
            }
        }
    }

    ret = PyUnicode_FromUnicode(output, outputpos);
    PyMem_DEL(output);
    return ret;
}

static PyMethodDef converterMethods[] =
{
    {"convert", (PyCFunction) convert, METH_VARARGS, 
     "Use the specified variant to convert the content."},
    {NULL, NULL, 0, NULL}
};

PyMODINIT_FUNC initconverter(void)
{
    Py_InitModule("converter", converterMethods);
}
